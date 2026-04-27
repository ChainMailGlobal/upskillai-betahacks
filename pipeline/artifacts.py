from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
import json


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


class ArtifactStore:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.stage_dir = run_dir / "stages"
        self.output_dir = run_dir / "outputs"
        self.prompt_dir = run_dir / "prompts"
        self.log_dir = run_dir / "logs"

        for directory in (self.run_dir, self.stage_dir, self.output_dir, self.prompt_dir, self.log_dir):
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def manifest_path(self) -> Path:
        return self.run_dir / "manifest.json"

    def load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"stages": {}}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def update_manifest(self, stage: str, status: str, **metadata: Any) -> None:
        manifest = self.load_manifest()
        manifest.setdefault("stages", {})[stage] = {"status": status, **_jsonable(metadata)}
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def stage_path(self, stage: str) -> Path:
        return self.stage_dir / f"{stage}.json"

    def stage_exists(self, stage: str) -> bool:
        return self.stage_path(stage).exists()

    def load_json(self, stage: str) -> dict[str, Any]:
        return json.loads(self.stage_path(stage).read_text(encoding="utf-8"))

    def save_json(self, stage: str, payload: dict[str, Any]) -> Path:
        path = self.stage_path(stage)
        path.write_text(json.dumps(_jsonable(payload), indent=2), encoding="utf-8")
        return path

    def save_text(self, relative_path: str, text: str) -> Path:
        path = self.run_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path
