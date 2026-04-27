from __future__ import annotations

from pathlib import Path
from typing import Any
import base64

from .modelark import ModelArkClient


def transcribe_audio(client: ModelArkClient, model: str, audio_path: Path) -> dict[str, Any]:
    response = client.post_multipart(
        "/audio/transcriptions",
        fields={"model": model},
        file_field="file",
        file_path=audio_path,
    )
    return response


def synthesize_speech(
    client: ModelArkClient,
    path: str,
    model: str,
    text: str,
    voice_id: str | None,
    output_path: Path,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "input": text,
        "format": "mp3",
    }
    if voice_id:
        payload["voice"] = voice_id

    raw = client.post_json_bytes(path, payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw)
    return {
        "output_path": str(output_path),
        "bytes": len(raw),
        "voice_id": voice_id,
        "preview_b64": base64.b64encode(raw[:64]).decode("ascii"),
    }
