from __future__ import annotations

from pathlib import Path
from typing import Any

from executors.seed_images import generate_image


def run(settings: Any, store: Any, client: Any, decompose_stage: dict[str, Any], force: bool = False) -> dict[str, Any]:
    stage = "storyboard"
    if store.stage_exists(stage) and not force:
        return store.load_json(stage)

    store.update_manifest(stage, "running")
    try:
        frames: list[dict[str, Any]] = []
        for step in decompose_stage["steps"]:
            prompt = step["prompt_for_keyframe"]
            prompt_file = store.save_text(
                f"prompts/storyboard_step_{step['step']:02d}.txt",
                prompt,
            )

            if settings.dry_run:
                frames.append(
                    {
                        "step": step["step"],
                        "title": step["title"],
                        "prompt_file": str(prompt_file),
                        "image_url": None,
                        "local_path": None,
                        "mode": "dry-run",
                    }
                )
                continue

            response = generate_image(client, settings.image_model, prompt)
            local_path = None
            image_url = response.get("url")
            if image_url:
                local_path = str(
                    client.download_file(
                        image_url,
                        store.output_dir / "storyboards" / f"step_{step['step']:02d}.png",
                    )
                )

            frames.append(
                {
                    "step": step["step"],
                    "title": step["title"],
                    "prompt_file": str(prompt_file),
                    "image_url": image_url,
                    "local_path": local_path,
                    "revised_prompt": response.get("revised_prompt"),
                }
            )

        payload = {
            "model": settings.image_model,
            "frames": frames,
        }
        store.save_json(stage, payload)
        store.update_manifest(stage, "completed", artifact=str(store.stage_path(stage)), frame_count=len(frames))
        return payload
    except Exception as exc:
        store.update_manifest(stage, "failed", error=str(exc))
        raise
