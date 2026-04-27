from __future__ import annotations

from typing import Any
import re

from executors.seed_chat import decompose_procedure
from pipeline.models import ProcedureStep


def run(
    settings: Any,
    store: Any,
    client: Any,
    transcript_stage: dict[str, Any],
    run_context: dict[str, Any] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    stage = "decompose"
    if store.stage_exists(stage) and not force:
        return store.load_json(stage)

    store.update_manifest(stage, "running")
    try:
        transcript = transcript_stage["transcript"]
        selected_lesson = (run_context or {}).get("selected_lesson")
        reference_context = _build_reference_context_string(run_context)
        if settings.dry_run:
            steps = _mock_steps(selected_lesson)
            payload = {
                "model": settings.chat_model,
                "steps": [step.to_dict() for step in steps],
                "source": "dry-run",
                "selected_lesson_id": selected_lesson.get("id") if selected_lesson else None,
            }
        else:
            response = decompose_procedure(
                client,
                settings.chat_model,
                transcript,
                step_count=_step_count_for_lesson(selected_lesson),
                reference_context=reference_context,
            )
            raw_steps = response.get("steps") or []
            steps = [_normalize_step(index + 1, raw_step) for index, raw_step in enumerate(raw_steps)]
            payload = {
                "model": settings.chat_model,
                "steps": [step.to_dict() for step in steps],
                "raw": response,
                "selected_lesson_id": selected_lesson.get("id") if selected_lesson else None,
            }

        store.save_json(stage, payload)
        store.update_manifest(stage, "completed", artifact=str(store.stage_path(stage)), step_count=len(payload["steps"]))
        return payload
    except Exception as exc:
        store.update_manifest(stage, "failed", error=str(exc))
        raise


def _normalize_step(index: int, raw: dict[str, Any]) -> ProcedureStep:
    return ProcedureStep(
        step=int(raw.get("step", index)),
        title=str(raw.get("title") or f"Step {index}"),
        action=str(raw.get("action") or ""),
        hazards=str(raw.get("hazards") or ""),
        prompt_for_keyframe=str(raw.get("prompt_for_keyframe") or raw.get("keyframe_prompt") or ""),
        motion_prompt=str(raw.get("motion_prompt") or ""),
        narration=str(raw.get("narration") or raw.get("action") or ""),
    )


def _mock_steps(selected_lesson: dict[str, Any] | None = None) -> list[ProcedureStep]:
    if not selected_lesson:
        return _default_mock_steps()

    beats = list(selected_lesson.get("overlay_beats", []))[:4]
    if not beats:
        return _default_mock_steps()

    scenario = selected_lesson.get("scenario", "Create a short AR training clip.")
    lesson_title = selected_lesson.get("title", "Micro Lesson")
    expert_gate = selected_lesson.get("expert_gate_required", False)
    backend = ", ".join(selected_lesson.get("backend_enrichment", [])[:2])
    risk_tail = (
        "This sequence must end with an escalation banner to a qualified expert."
        if expert_gate
        else "This sequence should end with a quick verification reminder."
    )
    steps: list[ProcedureStep] = []
    for index, beat in enumerate(beats, start=1):
        beat_title = _title_from_beat(beat)
        steps.append(
            ProcedureStep(
                step=index,
                title=beat_title,
                action=f"{scenario} Focus this beat on: {beat}.",
                hazards=_hazard_line(beat, expert_gate),
                prompt_for_keyframe=(
                    f"Photoreal AR training frame for '{lesson_title}'. {beat}. "
                    "Clean overlay labels, practical workshop context, 4:3 instructional composition."
                ),
                motion_prompt=(
                    f"Animate a concise training moment for '{lesson_title}'. {beat}. "
                    "Use clear arrows, step numbering, and a practical human-guided workflow."
                ),
                narration=f"Step {index}: {beat}. {risk_tail} Backend lookup cues: {backend}.",
            )
        )
    return steps


def _default_mock_steps() -> list[ProcedureStep]:
    return [
        ProcedureStep(
            step=1,
            title="De-Energize The Panel",
            action="Switch off the main breaker and verify the panel is isolated before opening it.",
            hazards="Residual voltage, false assumptions about breaker state, arc-flash exposure.",
            prompt_for_keyframe="Photoreal close-up of a master electrician shutting off a 200A main breaker, bright safety arrows, training-manual aesthetic, 4:3.",
            motion_prompt="Hands rotate the main breaker firmly to OFF, camera remains close and steady, workshop lighting, photoreal training-video motion.",
            narration="First thing: kill the main and confirm the panel is actually de-energized.",
        ),
        ProcedureStep(
            step=2,
            title="Confirm Zero Voltage",
            action="Use a multimeter to probe the lugs and confirm there is no live voltage.",
            hazards="Live lugs, improper probe placement, one-handed safety violations.",
            prompt_for_keyframe="Photoreal panel interior with multimeter probes touching the lugs, bold red callouts for probe placement, 4:3, safety-training visual.",
            motion_prompt="Multimeter probes touch the lugs in sequence, meter steadies in frame, subtle handheld realism, clean instructional pacing.",
            narration="Never trust the breaker alone. Meter the lugs and confirm zero voltage yourself.",
        ),
        ProcedureStep(
            step=3,
            title="Open And Inspect",
            action="Remove the panel cover and inspect for heat damage, corrosion, or loose terminations.",
            hazards="Sharp panel edges, hidden damage, loose conductors under tension.",
            prompt_for_keyframe="Exploded-view style panel cover removal with highlighted screws and warning labels, photoreal, 4:3.",
            motion_prompt="The panel face loosens and lifts away, revealing the interior while hazard callouts animate on screen.",
            narration="Open the panel cleanly and inspect before you touch any conductor.",
        ),
        ProcedureStep(
            step=4,
            title="Land The Circuit",
            action="Route and terminate the new circuit with proper spacing, torque, and conductor discipline.",
            hazards="Loose lugs, wire nicking, improper bend radius, overcrowding.",
            prompt_for_keyframe="Master electrician landing a new circuit into a residential breaker panel, color-coded conductors, torque callouts, photoreal 4:3 training visual.",
            motion_prompt="Hands guide the conductor into place, tighten the lug with measured force, labels pulse on torque and spacing.",
            narration="Land the circuit deliberately. Clean routing and proper torque matter as much as the connection itself.",
        ),
        ProcedureStep(
            step=5,
            title="Reassemble Safely",
            action="Replace the panel cover, confirm tool clearance, and restore the assembly to service condition.",
            hazards="Pinched conductors, misaligned cover, leftover tools in the enclosure.",
            prompt_for_keyframe="Panel cover being reinstalled with final checklist overlays, photoreal instructional style, 4:3.",
            motion_prompt="Panel cover slides back into place, screws seat evenly, on-screen checklist items confirm safe closure.",
            narration="Close it up methodically. No pinched wires, no missing screws, no surprises.",
        ),
        ProcedureStep(
            step=6,
            title="Restore Power And Validate",
            action="Re-energize the panel, observe startup conditions, and validate the load under watch.",
            hazards="Unexpected load behavior, nuisance trips, thermal issues after energizing.",
            prompt_for_keyframe="Electrician restoring power and observing panel startup, meter readings visible, training-video look, 4:3.",
            motion_prompt="Breaker returns to ON, status indicators settle, the electrician observes the load while a final green confirmation marker appears.",
            narration="Restore power and watch the load. The job is not done until the panel proves it under operation.",
        ),
    ]


def _build_reference_context_string(run_context: dict[str, Any] | None) -> str | None:
    if not run_context:
        return None

    pack = run_context.get("selected_pack")
    lesson = run_context.get("selected_lesson")
    if not pack and not lesson:
        return None

    lines = [
        f"Experience mode: {run_context.get('experience_mode', 'learn')}",
        f"Source strategy: {run_context.get('source_strategy', 'text-first')}",
    ]
    if pack:
        lines.append(f"Trade pack: {pack.get('title')}")
        lines.append(f"Pack summary: {pack.get('summary')}")
    if lesson:
        lines.append(f"Lesson title: {lesson.get('title')}")
        lines.append(f"Scenario: {lesson.get('scenario')}")
        lines.append(f"Expert gate required: {lesson.get('expert_gate_required')}")
        lines.append("Overlay beats:")
        for beat in lesson.get("overlay_beats", []):
            lines.append(f"- {beat}")
    return "\n".join(lines)


def _step_count_for_lesson(selected_lesson: dict[str, Any] | None) -> int:
    if not selected_lesson:
        return 6
    beats = selected_lesson.get("overlay_beats", [])
    return max(4, min(8, len(beats) if beats else 6))


def _title_from_beat(beat: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9 ]+", " ", beat).strip()
    words = cleaned.split()
    if not words:
        return "Instruction Step"
    return " ".join(word.capitalize() for word in words[:5])


def _hazard_line(beat: str, expert_gate: bool) -> str:
    if expert_gate:
        return f"High-risk workflow. Do not imply real-world action without qualified supervision. Visual focus: {beat}."
    return f"Low-risk workflow with basic PPE and area-prep reminders. Visual focus: {beat}."
