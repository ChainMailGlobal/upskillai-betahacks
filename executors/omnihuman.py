from __future__ import annotations

from typing import Any

from .modelark import ModelArkClient
from .seed_video import poll_video_task


def create_omnihuman_task(
    client: ModelArkClient,
    path: str,
    model: str,
    image_url: str,
    audio_url: str,
    resolution: str = "720p",
    prompt: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "image_url": image_url,
        "audio_url": audio_url,
        "resolution": resolution,
    }
    if prompt:
        payload["prompt"] = prompt
    return client.post_json(path, payload)


def poll_omnihuman_task(
    client: ModelArkClient,
    path: str,
    task_id: str,
    poll_interval_sec: float,
    timeout_sec: float,
) -> dict[str, Any]:
    return poll_video_task(client, path, task_id, poll_interval_sec, timeout_sec)
