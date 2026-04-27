from __future__ import annotations

import argparse

from catalog import build_reference_context, build_run_context
from executors import ModelArkClient
from pipeline import ArtifactStore
from pipeline import animate, decompose, digital_twin, stitch, storyboard, transcribe, voice
from settings import Settings


def parse_args() -> argparse.Namespace:
    stage_choices = ["transcribe", "decompose", "storyboard", "animate", "voice", "digital_twin", "stitch"]
    parser = argparse.ArgumentParser(description="Run the UpSkillAI BetaHacks pipeline.")
    parser.add_argument("--run-name", required=True, help="Directory name under runs/.")
    parser.add_argument("--mode", choices=["learn", "assist"], default="learn", help="Product mode to run.")
    parser.add_argument(
        "--source-strategy",
        choices=["text-first", "balanced", "video-first"],
        default="text-first",
        help="How strongly the run prefers text sources over visual references.",
    )
    parser.add_argument("--reference-pack", help="Trade reference pack id from reference_library.json.")
    parser.add_argument("--lesson-id", help="Micro-lesson id inside the selected trade pack.")
    parser.add_argument("--input-audio", help="Master tradesperson audio file.")
    parser.add_argument("--input-video", help="Optional master recording video file.")
    parser.add_argument("--stan-portrait", help="Portrait image for OmniHuman.")
    parser.add_argument("--stan-voice-sample", help="Optional voice sample for future voice-clone workflows.")
    parser.add_argument("--dry-run", action="store_true", help="Skip live API calls and write mock artifacts instead.")
    parser.add_argument(
        "--force-stage",
        choices=stage_choices,
        help="Force rerun from the selected stage onward.",
    )
    parser.add_argument(
        "--stop-after",
        choices=stage_choices,
        help="Stop after the selected stage completes. Useful for incremental smoke tests.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_args(args)
    settings.validate_for_live_mode()

    store = ArtifactStore(settings.run_dir)
    client = None
    if not settings.dry_run:
        client = ModelArkClient(settings.byteplus_api_key, settings.byteplus_base_url, settings.request_timeout_sec)

    run_context = build_run_context(
        experience_mode=settings.experience_mode,
        source_strategy=settings.source_strategy,
        reference_pack_id=settings.reference_pack_id,
        lesson_id=settings.lesson_id,
    )
    run_context_path = store.save_json("run_context", run_context)
    store.update_manifest("run_context", "completed", artifact=str(run_context_path))

    force_from = args.force_stage
    stage_order = ["transcribe", "decompose", "storyboard", "animate", "voice", "digital_twin", "stitch"]
    force_flags = {stage: False for stage in stage_order}
    if force_from:
        enabled = False
        for stage in stage_order:
            if stage == force_from:
                enabled = True
            if enabled:
                force_flags[stage] = True

    transcript_stage = transcribe.run(settings, store, client, force=force_flags["transcribe"])
    if args.stop_after == "transcribe":
        _print_summary(settings, store, run_context=run_context, transcript_stage=transcript_stage)
        return

    decompose_stage = decompose.run(
        settings,
        store,
        client,
        transcript_stage,
        run_context=run_context,
        force=force_flags["decompose"],
    )
    if args.stop_after == "decompose":
        _print_summary(
            settings,
            store,
            run_context=run_context,
            transcript_stage=transcript_stage,
            decompose_stage=decompose_stage,
        )
        return

    storyboard_stage = storyboard.run(settings, store, client, decompose_stage, force=force_flags["storyboard"])
    if args.stop_after == "storyboard":
        _print_summary(
            settings,
            store,
            run_context=run_context,
            transcript_stage=transcript_stage,
            decompose_stage=decompose_stage,
            storyboard_stage=storyboard_stage,
        )
        return

    clips_stage = animate.run(
        settings,
        store,
        client,
        decompose_stage,
        storyboard_stage,
        force=force_flags["animate"],
    )
    if args.stop_after == "animate":
        _print_summary(
            settings,
            store,
            run_context=run_context,
            transcript_stage=transcript_stage,
            decompose_stage=decompose_stage,
            storyboard_stage=storyboard_stage,
            clips_stage=clips_stage,
        )
        return

    voice_stage = voice.run(settings, store, client, decompose_stage, force=force_flags["voice"])
    if args.stop_after == "voice":
        _print_summary(
            settings,
            store,
            run_context=run_context,
            transcript_stage=transcript_stage,
            decompose_stage=decompose_stage,
            storyboard_stage=storyboard_stage,
            clips_stage=clips_stage,
            voice_stage=voice_stage,
        )
        return

    twin_stage = digital_twin.run(settings, store, client, voice_stage, force=force_flags["digital_twin"])
    if args.stop_after == "digital_twin":
        _print_summary(
            settings,
            store,
            run_context=run_context,
            transcript_stage=transcript_stage,
            decompose_stage=decompose_stage,
            storyboard_stage=storyboard_stage,
            clips_stage=clips_stage,
            voice_stage=voice_stage,
            twin_stage=twin_stage,
        )
        return

    stitch_stage = stitch.run(
        settings,
        store,
        clips_stage,
        voice_stage,
        twin_stage,
        force=force_flags["stitch"],
    )

    _print_summary(
        settings,
        store,
        run_context=run_context,
        transcript_stage=transcript_stage,
        decompose_stage=decompose_stage,
        storyboard_stage=storyboard_stage,
        clips_stage=clips_stage,
        voice_stage=voice_stage,
        twin_stage=twin_stage,
        stitch_stage=stitch_stage,
    )


def _print_summary(
    settings: Settings,
    store: ArtifactStore,
    *,
    run_context: dict | None = None,
    transcript_stage: dict | None = None,
    decompose_stage: dict | None = None,
    storyboard_stage: dict | None = None,
    clips_stage: dict | None = None,
    voice_stage: dict | None = None,
    twin_stage: dict | None = None,
    stitch_stage: dict | None = None,
) -> None:
    print(f"Run complete: {settings.run_dir}")
    print(f"Manifest: {store.manifest_path}")
    if run_context:
        selected_pack = (run_context.get("selected_pack") or {}).get("id")
        selected_lesson = (run_context.get("selected_lesson") or {}).get("id")
        print(f"Mode: {settings.experience_mode}")
        print(f"Source strategy: {settings.source_strategy}")
        print(f"Reference pack: {selected_pack or 'none'}")
        print(f"Lesson: {selected_lesson or 'none'}")
    if transcript_stage:
        print(f"Transcript chars: {len(transcript_stage['transcript'])}")
    if decompose_stage:
        print(f"Procedure steps: {len(decompose_stage['steps'])}")
    if storyboard_stage:
        print(f"Storyboard frames: {len(storyboard_stage['frames'])}")
    if clips_stage:
        print(f"Animated clips: {len(clips_stage['clips'])}")
    if voice_stage:
        print(f"Voice output: {voice_stage.get('audio_path') or 'planned only'}")
    if twin_stage:
        print(f"Digital twin output: {twin_stage.get('video_path') or 'planned only'}")
    if stitch_stage:
        print(f"Submission output: {stitch_stage.get('submission_path') or 'planned only'}")


if __name__ == "__main__":
    main()
