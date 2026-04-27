from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a BytePlus Seed submission package from an orchestrator run."
    )
    parser.add_argument("--run-name", required=True, help="Directory name under runs/.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent
    run_dir = project_root / "runs" / args.run_name
    stage_dir = run_dir / "stages"
    output_dir = run_dir / "outputs"
    submission_dir = run_dir / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)

    manifest = _load_json(run_dir / "manifest.json")
    stage_payloads = {
        stage_name: _safe_load_json(stage_dir / f"{stage_name}.json")
        for stage_name in (
            "run_context",
            "transcribe",
            "decompose",
            "storyboard",
            "animate",
            "voice",
            "digital_twin",
            "stitch",
        )
    }

    summary = build_summary(
        run_name=args.run_name,
        run_dir=run_dir,
        output_dir=output_dir,
        manifest=manifest,
        stage_payloads=stage_payloads,
    )
    talk_track = build_talk_track(summary)

    summary_path = submission_dir / "byteplus_submission_summary.json"
    talk_track_path = submission_dir / "byteplus_talk_track.md"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    talk_track_path.write_text(talk_track, encoding="utf-8")

    print(f"Submission summary: {summary_path}")
    print(f"Talk track: {talk_track_path}")
    print(f"Compliance: {summary['compliance']['status']}")
    print(f"Live demo source: {summary['demo_sections']['live_demo']['primary_showpiece']}")


def build_summary(
    *,
    run_name: str,
    run_dir: Path,
    output_dir: Path,
    manifest: dict[str, Any],
    stage_payloads: dict[str, dict[str, Any] | None],
) -> dict[str, Any]:
    run_context = stage_payloads.get("run_context") or {}
    selected_pack = (run_context.get("selected_pack") or {}).get("id")
    selected_lesson = (run_context.get("selected_lesson") or {}).get("id")

    models_used = {
        "Seed 2.0 / Seed chat": _model_name(stage_payloads.get("decompose")),
        "Seedream 5.0": _model_name(stage_payloads.get("storyboard")),
        "Seedance 2.0": _model_name(stage_payloads.get("animate")),
        "Seed Speech": _join_models(
            _model_name(stage_payloads.get("transcribe")),
            _model_name(stage_payloads.get("voice")),
        ),
        "OmniHuman": _model_name(stage_payloads.get("digital_twin")),
    }

    compliance = evaluate_compliance(manifest=manifest, stage_payloads=stage_payloads)

    storyboard_assets = _collect_existing_files(output_dir / "storyboards")
    animated_assets = _collect_existing_files(output_dir / "clips")
    voice_asset = (stage_payloads.get("voice") or {}).get("audio_path")
    twin_asset = (stage_payloads.get("digital_twin") or {}).get("video_path")
    stitch_asset = (stage_payloads.get("stitch") or {}).get("submission_path")

    return {
        "run_name": run_name,
        "run_dir": str(run_dir),
        "mode": run_context.get("experience_mode"),
        "source_strategy": run_context.get("source_strategy"),
        "reference_pack": selected_pack,
        "lesson_id": selected_lesson,
        "models_used": models_used,
        "compliance": compliance,
        "assets": {
            "storyboards": storyboard_assets,
            "animated_clips": animated_assets,
            "voiceover": voice_asset,
            "digital_twin": twin_asset,
            "submission_video": stitch_asset,
        },
        "demo_sections": {
            "live_demo": {
                "time": "0:00-1:00",
                "goal": "Show the BytePlus-generated experience first.",
                "primary_showpiece": (
                    animated_assets[0]
                    if animated_assets
                    else (twin_asset or "No animated clip generated yet.")
                ),
                "supporting_assets": [path for path in [voice_asset, twin_asset, stitch_asset] if path],
            },
            "technical_architecture": {
                "time": "1:00-1:30",
                "goal": "Show the pipeline stages and exact Seed / OmniHuman model connections.",
                "show_files": [
                    str(run_dir / "manifest.json"),
                    str(run_dir / "stages" / "run_context.json"),
                    str(run_dir / "stages" / "decompose.json"),
                    str(run_dir / "stages" / "storyboard.json"),
                    str(run_dir / "stages" / "animate.json"),
                ],
            },
            "vision": {
                "time": "1:30-2:00",
                "goal": "Show the future path into Spectacles, remote experts, and OEM/code lookups.",
                "show_files": [
                    str(Path(__file__).resolve().parent / "docs" / "product_modes.md"),
                    str(Path(__file__).resolve().parent / "README.md"),
                ],
            },
        },
    }


def evaluate_compliance(
    *,
    manifest: dict[str, Any],
    stage_payloads: dict[str, dict[str, Any] | None],
) -> dict[str, Any]:
    stages = manifest.get("stages") or {}
    completed = {name for name, info in stages.items() if (info or {}).get("status") == "completed"}
    dry_run_markers = []
    for stage_name, payload in stage_payloads.items():
        if _stage_is_dry_run(stage_name, payload):
            dry_run_markers.append(stage_name)

    required_tools_present = {
        "Seed 2.0 / Seed chat": "decompose" in completed,
        "Seedream 5.0": "storyboard" in completed,
        "Seedance 2.0": "animate" in completed,
        "Seed Speech": "transcribe" in completed or "voice" in completed,
        "OmniHuman": "digital_twin" in completed,
    }
    live_byteplus_video_generated = _has_live_animate_outputs(
        completed=completed,
        animate_payload=stage_payloads.get("animate"),
    )

    issues: list[str] = []
    if not live_byteplus_video_generated:
        issues.append("No live Seedance clip has been generated in this run yet.")
    if dry_run_markers:
        issues.append(
            "This run includes dry-run stages: " + ", ".join(sorted(set(dry_run_markers))) + "."
        )

    status = "ready" if live_byteplus_video_generated else "incomplete"
    return {
        "status": status,
        "video_generation_vendor": "BytePlus Seed models only",
        "required_tools_present": required_tools_present,
        "dry_run_stages": sorted(set(dry_run_markers)),
        "issues": issues,
    }


def _stage_is_dry_run(stage_name: str, payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False
    if payload.get("mode") == "dry-run" or payload.get("source") == "dry-run":
        return True
    if stage_name == "storyboard":
        frames = payload.get("frames") or []
        return bool(frames) and all(frame.get("mode") == "dry-run" for frame in frames)
    if stage_name == "animate":
        clips = payload.get("clips") or []
        return bool(clips) and all(clip.get("mode") == "dry-run" for clip in clips)
    return False


def _has_live_animate_outputs(
    *,
    completed: set[str],
    animate_payload: dict[str, Any] | None,
) -> bool:
    if "animate" not in completed or not animate_payload or _stage_is_dry_run("animate", animate_payload):
        return False
    clips = animate_payload.get("clips") or []
    for clip in clips:
        if clip.get("local_path") or clip.get("video_url"):
            return True
    return False


def build_talk_track(summary: dict[str, Any]) -> str:
    compliance = summary["compliance"]
    models = summary["models_used"]
    assets = summary["assets"]
    live_demo_asset = summary["demo_sections"]["live_demo"]["primary_showpiece"]
    lines = [
        "# BytePlus Submission Talk Track",
        "",
        "## 0:00-1:00 Live Demo",
        "",
        f"Lead with: `{live_demo_asset}`",
        "",
        "Say:",
        "",
        (
            "This is UpSkillAI. We use BytePlus Seed models to turn trusted trade instructions into "
            "byte-sized AR-style field lessons, and we extend the same graph into live assist workflows "
            "for Spectacles or phone."
        ),
        "",
        "If available, show in this order:",
    ]
    for path in assets["animated_clips"][:3]:
        lines.append(f"- `{path}`")
    if assets["digital_twin"]:
        lines.append(f"- `{assets['digital_twin']}`")
    if assets["voiceover"]:
        lines.append(f"- `{assets['voiceover']}`")

    lines.extend(
        [
            "",
            "## 1:00-1:30 Technical Architecture",
            "",
            "Say:",
            "",
            (
                f"We analyze and structure the lesson with {models['Seed 2.0 / Seed chat'] or 'Seed chat'}, "
                f"generate keyframes with {models['Seedream 5.0'] or 'Seedream'}, "
                f"animate clips with {models['Seedance 2.0'] or 'Seedance'}, "
                f"generate narration with {models['Seed Speech'] or 'Seed Speech'}, "
                f"and render the digital human with {models['OmniHuman'] or 'OmniHuman'}."
            ),
            "",
            "Show these files:",
        ]
    )
    for path in summary["demo_sections"]["technical_architecture"]["show_files"]:
        lines.append(f"- `{path}`")

    lines.extend(
        [
            "",
            "## 1:30-2:00 Vision",
            "",
            "Say:",
            "",
            (
                "Beyond the hackathon, the same lesson graph drives hands-free remote expert support, "
                "AI overlays on real equipment, and backend lookups for OEM manuals, codes, permits, and checklists."
            ),
            "",
            "## Compliance",
            "",
            f"- Status: `{compliance['status']}`",
            f"- BytePlus-only video generation: `{compliance['video_generation_vendor']}`",
        ]
    )
    for issue in compliance["issues"]:
        lines.append(f"- Open issue: {issue}")

    return "\n".join(lines) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_existing_files(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    return [str(path) for path in sorted(directory.glob("*")) if path.is_file()]


def _model_name(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    value = payload.get("model")
    return str(value) if value else None


def _join_models(*values: str | None) -> str | None:
    present = [value for value in values if value]
    if not present:
        return None
    unique: list[str] = []
    for value in present:
        if value not in unique:
            unique.append(value)
    return " + ".join(unique)


if __name__ == "__main__":
    main()
