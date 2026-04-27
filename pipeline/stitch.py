from __future__ import annotations

from pathlib import Path
from typing import Any
import shutil
import subprocess


def run(
    settings: Any,
    store: Any,
    clips_stage: dict[str, Any],
    voice_stage: dict[str, Any],
    twin_stage: dict[str, Any],
    force: bool = False,
) -> dict[str, Any]:
    stage = "stitch"
    if store.stage_exists(stage) and not force:
        return store.load_json(stage)

    store.update_manifest(stage, "running")
    try:
        clip_paths = [clip.get("local_path") for clip in clips_stage["clips"] if clip.get("local_path")]
        twin_path = twin_stage.get("video_path")
        if twin_path:
            clip_paths.append(twin_path)

        shotlist_path = _write_shotlist(store, clip_paths)
        ffmpeg = shutil.which("ffmpeg")
        output_path = store.output_dir / "submission.mp4"

        if settings.dry_run or not ffmpeg or not clip_paths:
            payload = {
                "mode": "planned",
                "ffmpeg_found": bool(ffmpeg),
                "shotlist_path": str(shotlist_path),
                "voice_path": voice_stage.get("audio_path"),
                "submission_path": None,
            }
        else:
            cmd = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(shotlist_path),
                "-c",
                "copy",
                str(output_path),
            ]
            subprocess.run(cmd, check=True)
            payload = {
                "mode": "rendered",
                "ffmpeg_found": True,
                "shotlist_path": str(shotlist_path),
                "voice_path": voice_stage.get("audio_path"),
                "submission_path": str(output_path),
            }

        store.save_json(stage, payload)
        store.update_manifest(stage, "completed", artifact=str(store.stage_path(stage)), submission_path=payload.get("submission_path"))
        return payload
    except Exception as exc:
        store.update_manifest(stage, "failed", error=str(exc))
        raise


def _write_shotlist(store: Any, clip_paths: list[str]) -> Path:
    lines = []
    for clip_path in clip_paths:
        path = Path(clip_path).resolve()
        lines.append(f"file '{path.as_posix()}'")
    shotlist_path = store.run_dir / "shotlist.txt"
    shotlist_path.write_text("\n".join(lines), encoding="utf-8")
    return shotlist_path
