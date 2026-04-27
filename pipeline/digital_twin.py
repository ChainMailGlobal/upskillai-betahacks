from __future__ import annotations

from typing import Any

from executors.omnihuman import create_omnihuman_task, poll_omnihuman_task


def run(settings: Any, store: Any, client: Any, voice_stage: dict[str, Any], force: bool = False) -> dict[str, Any]:
    stage = "digital_twin"
    if store.stage_exists(stage) and not force:
        return store.load_json(stage)

    store.update_manifest(stage, "running")
    try:
        if settings.dry_run:
            payload = {
                "model": settings.omnihuman_model,
                "portrait_path": str(settings.stan_portrait),
                "audio_path": voice_stage.get("audio_path"),
                "video_path": None,
                "mode": "dry-run",
            }
        else:
            if not settings.stan_portrait or not settings.stan_portrait.exists():
                raise RuntimeError("A portrait image is required for OmniHuman live mode.")
            if not voice_stage.get("audio_path"):
                raise RuntimeError("Voice stage must produce audio before OmniHuman can run.")

            created = create_omnihuman_task(
                client,
                settings.omnihuman_create_path,
                settings.omnihuman_model,
                image_url=settings.stan_portrait.as_uri(),
                audio_url=str(voice_stage["audio_path"]),
                resolution="720p",
                prompt="Master tradesperson speaking directly to camera in a calm, practical workshop environment.",
            )
            task_id = str(created.get("task_id") or created.get("id"))
            polled = poll_omnihuman_task(
                client,
                settings.omnihuman_retrieve_path,
                task_id,
                settings.poll_interval_sec,
                settings.request_timeout_sec,
            )
            video_url = _extract_url(polled)
            local_path = None
            if video_url:
                local_path = str(client.download_file(video_url, store.output_dir / "omnihuman" / "stan_twin.mp4"))

            payload = {
                "model": settings.omnihuman_model,
                "task_id": task_id,
                "portrait_path": str(settings.stan_portrait),
                "audio_path": voice_stage.get("audio_path"),
                "video_url": video_url,
                "video_path": local_path,
            }

        store.save_json(stage, payload)
        store.update_manifest(stage, "completed", artifact=str(store.stage_path(stage)))
        return payload
    except Exception as exc:
        store.update_manifest(stage, "failed", error=str(exc))
        raise


def _extract_url(response: dict[str, Any]) -> str | None:
    for key in ("video_url", "url", "download_url"):
        if response.get(key):
            return str(response[key])
    data = response.get("data")
    if isinstance(data, dict):
        for key in ("video_url", "url", "download_url"):
            if data.get(key):
                return str(data[key])
    return None
