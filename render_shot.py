from __future__ import annotations

import argparse

from executors import ModelArkClient
from pipeline import ArtifactStore
from pipeline.animate import rerender_single_step
from pipeline.storyboard import run as storyboard_run
from settings import Settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rerender one storyboard + animation shot.")
    parser.add_argument("--run-name", required=True, help="Existing run directory name under runs/.")
    parser.add_argument("--step", type=int, required=True, help="1-based procedure step number.")
    parser.add_argument("--dry-run", action="store_true", help="Skip live API calls and write prompt artifacts only.")
    parser.add_argument("--stan-portrait", help="Optional portrait override.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_args(args)
    store = ArtifactStore(settings.run_dir)
    client = None
    if not settings.dry_run:
        settings.validate_for_live_mode()
        client = ModelArkClient(settings.byteplus_api_key, settings.byteplus_base_url, settings.request_timeout_sec)

    decompose_stage = store.load_json("decompose")
    storyboard_stage = storyboard_run(settings, store, client, decompose_stage, force=False)

    step = next((item for item in decompose_stage["steps"] if int(item["step"]) == args.step), None)
    if not step:
        raise SystemExit(f"Step {args.step} not found in decompose stage.")

    frame = next((item for item in storyboard_stage["frames"] if int(item["step"]) == args.step), None)
    if not frame:
        raise SystemExit(f"Step {args.step} not found in storyboard stage.")

    result = rerender_single_step(settings, store, client, step, frame)
    store.save_json(f"rerender_step_{args.step:02d}", result)
    print(f"Rerender artifact: {store.stage_path(f'rerender_step_{args.step:02d}')}")


if __name__ == "__main__":
    main()
