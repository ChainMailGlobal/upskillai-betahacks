from __future__ import annotations

from typing import Any

from executors.seed_video import create_video_task, poll_video_task


def run(
    settings: Any,
    store: Any,
    client: Any,
    decompose_stage: dict[str, Any],
    storyboard_stage: dict[str, Any],
    force: bool = False,
) -> dict[str, Any]:
    stage = "animate"
    if store.stage_exists(stage) and not force:
        return store.load_json(stage)

    store.update_manifest(stage, "running")
    try:
        frames_by_step = {frame["step"]: frame for frame in storyboard_stage["frames"]}
        clips: list[dict[str, Any]] = []

        for step in decompose_stage["steps"]:
            frame = frames_by_step[step["step"]]
            motion_prompt_file = store.save_text(
                f"prompts/animate_step_{step['step']:02d}.txt",
                step["motion_prompt"],
            )

            if settings.dry_run:
                clips.append(
                    {
                        "step": step["step"],
                        "title": step["title"],
                        "motion_prompt_file": str(motion_prompt_file),
                        "task_id": None,
                        "video_url": None,
                        "local_path": None,
                        "mode": "dry-run",
                    }
                )
                continue

            created = create_video_task(
                client,
                settings.seed_video_create_path,
                settings.video_model,
                step["motion_prompt"],
                resolution="720p",
                duration=5,
                aspect_ratio="16:9",
                first_frame_url=frame.get("image_url"),
            )
            task_id = str(created.get("task_id") or created.get("id"))
            polled = poll_video_task(
                client,
                settings.seed_video_retrieve_path,
                task_id,
                settings.poll_interval_sec,
                settings.request_timeout_sec,
            )
            video_url = _extract_url(polled)
            local_path = None
            if video_url:
                local_path = str(
                    client.download_file(
                        video_url,
                        store.output_dir / "clips" / f"step_{step['step']:02d}.mp4",
                    )
                )

            clips.append(
                {
                    "step": step["step"],
                    "title": step["title"],
                    "motion_prompt_file": str(motion_prompt_file),
                    "task_id": task_id,
                    "video_url": video_url,
                    "local_path": local_path,
                }
            )

        payload = {
            "model": settings.video_model,
            "clips": clips,
        }
        store.save_json(stage, payload)
        store.update_manifest(stage, "completed", artifact=str(store.stage_path(stage)), clip_count=len(clips))
        return payload
    except Exception as exc:
        store.update_manifest(stage, "failed", error=str(exc))
        raise


def rerender_single_step(
    settings: Any,
    store: Any,
    client: Any,
    step: dict[str, Any],
    frame: dict[str, Any],
) -> dict[str, Any]:
    motion_prompt_file = store.save_text(
        f"prompts/rerender_step_{step['step']:02d}.txt",
        step["motion_prompt"],
    )
    if settings.dry_run:
        return {
            "step": step["step"],
            "title": step["title"],
            "motion_prompt_file": str(motion_prompt_file),
            "task_id": None,
            "video_url": None,
            "local_path": None,
            "mode": "dry-run",
        }

    created = create_video_task(
        client,
        settings.seed_video_create_path,
        settings.video_model,
        step["motion_prompt"],
        resolution="720p",
        duration=5,
        aspect_ratio="16:9",
        first_frame_url=frame.get("image_url"),
    )
    task_id = str(created.get("task_id") or created.get("id"))
    polled = poll_video_task(
        client,
        settings.seed_video_retrieve_path,
        task_id,
        settings.poll_interval_sec,
        settings.request_timeout_sec,
    )
    video_url = _extract_url(polled)
    local_path = None
    if video_url:
        local_path = str(
            client.download_file(
                video_url,
                store.output_dir / "clips" / f"step_{step['step']:02d}_rerender.mp4",
            )
        )
    return {
        "step": step["step"],
        "title": step["title"],
        "motion_prompt_file": str(motion_prompt_file),
        "task_id": task_id,
        "video_url": video_url,
        "local_path": local_path,
    }


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
