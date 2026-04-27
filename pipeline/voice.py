from __future__ import annotations

from typing import Any

from executors.seed_speech import synthesize_speech


def run(settings: Any, store: Any, client: Any, decompose_stage: dict[str, Any], force: bool = False) -> dict[str, Any]:
    stage = "voice"
    if store.stage_exists(stage) and not force:
        return store.load_json(stage)

    store.update_manifest(stage, "running")
    try:
        script = "\n".join(step["narration"] for step in decompose_stage["steps"])
        script_path = store.save_text("outputs/voiceover_script.txt", script)

        if settings.dry_run:
            payload = {
                "model": settings.tts_model,
                "voice_id": settings.seed_voice_id,
                "script_path": str(script_path),
                "audio_path": None,
                "mode": "dry-run",
            }
        else:
            audio_path = store.output_dir / "voice" / "voiceover.mp3"
            response = synthesize_speech(
                client,
                settings.seed_tts_path,
                settings.tts_model,
                script,
                settings.seed_voice_id,
                audio_path,
            )
            payload = {
                "model": settings.tts_model,
                "voice_id": settings.seed_voice_id,
                "script_path": str(script_path),
                "audio_path": response["output_path"],
                "raw": response,
            }

        store.save_json(stage, payload)
        store.update_manifest(stage, "completed", artifact=str(store.stage_path(stage)))
        return payload
    except Exception as exc:
        store.update_manifest(stage, "failed", error=str(exc))
        raise
