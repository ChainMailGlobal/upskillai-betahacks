from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ProcedureStep:
    step: int
    title: str
    action: str
    hazards: str
    prompt_for_keyframe: str
    motion_prompt: str
    narration: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
