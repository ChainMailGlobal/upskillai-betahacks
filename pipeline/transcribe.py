from __future__ import annotations

from pathlib import Path
from typing import Any
import shutil
import subprocess

from executors.seed_speech import transcribe_audio


DRY_RUN_TRANSCRIPT = """\
Stan begins by explaining that the first move is to shut off the main breaker before
touching the panel. He confirms zero voltage with a meter, removes the panel cover,
checks for heat damage and loose lugs, then lands the new circuit carefully while calling
out torque, PPE, and lockout safety. He closes by restoring power and validating the
load under observation.
"""


def run(settings: Any, store: Any, client: Any, force: bool = False) -> dict[str, Any]:
    stage = "transcribe"
    if store.stage_exists(stage) and not force:
        return store.load_json(stage)

    store.update_manifest(stage, "running")
    try:
        if settings.dry_run:
            payload = {
                "model": settings.asr_model,
                "transcript": DRY_RUN_TRANSCRIPT.strip(),
                "source": "dry-run",
            }
        else:
            audio_path, source_info = _resolve_audio_input(settings, store)
            response = transcribe_audio(client, settings.asr_model, audio_path)
            transcript = response.get("text") or response.get("transcript") or response.get("result") or ""
            payload = {
                "model": settings.asr_model,
                "transcript": transcript.strip(),
                "source": source_info,
                "transcription_input": str(audio_path),
                "raw": response,
            }

        store.save_json(stage, payload)
        store.update_manifest(stage, "completed", artifact=str(store.stage_path(stage)))
        return payload
    except Exception as exc:
        store.update_manifest(stage, "failed", error=str(exc))
        raise


def _resolve_audio_input(settings: Any, store: Any) -> tuple[Path, dict[str, Any]]:
    if settings.input_audio and settings.input_audio.exists():
        return settings.input_audio, {
            "mode": "audio",
            "input_audio": str(settings.input_audio),
        }

    if settings.input_video and settings.input_video.exists():
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(
                "ffmpeg is required to extract audio from the supplied video input."
            )

        derived_audio = store.output_dir / "derived" / "master_recording_from_video.wav"
        derived_audio.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(settings.input_video),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(derived_audio),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise RuntimeError(
                f"ffmpeg failed to extract audio from {settings.input_video}: {stderr or exc}"
            ) from exc

        return derived_audio, {
            "mode": "video->audio",
            "input_video": str(settings.input_video),
            "derived_audio": str(derived_audio),
        }

    raise RuntimeError("No usable input audio or video file was found for transcription.")
