from __future__ import annotations

from typing import Any
import time

from .modelark import ModelArkClient


def create_video_task(
    client: ModelArkClient,
    path: str,
    model: str,
    prompt: str,
    *,
    resolution: str = "720p",
    duration: int = 5,
    aspect_ratio: str = "16:9",
    first_frame_url: str | None = None,
    reference_image_urls: list[str] | None = None,
    reference_video_urls: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "resolution": resolution,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
    }
    if first_frame_url:
        payload["first_frame"] = first_frame_url
    if reference_image_urls:
        payload["reference_images"] = reference_image_urls
    if reference_video_urls:
        payload["reference_videos"] = reference_video_urls
    return client.post_json(path, payload)


def poll_video_task(
    client: ModelArkClient,
    path: str,
    task_id: str,
    poll_interval_sec: float,
    timeout_sec: float,
) -> dict[str, Any]:
    deadline = time.time() + timeout_sec
    last_response: dict[str, Any] | None = None

    while time.time() < deadline:
        last_response = client.get_json(path, {"task_id": task_id})
        status = (last_response.get("status") or "").lower()
        if status in {"completed", "succeeded", "success"}:
            return last_response
        if status in {"failed", "error", "cancelled"}:
            raise RuntimeError(f"Video task failed: {last_response}")
        time.sleep(poll_interval_sec)

    raise TimeoutError(f"Timed out polling video task {task_id}: {last_response}")
