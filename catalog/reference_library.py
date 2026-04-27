from __future__ import annotations

from pathlib import Path
from typing import Any
import json


LIBRARY_PATH = Path(__file__).with_name("reference_library.json")


def load_library() -> dict[str, Any]:
    return json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))


def get_pack(library: dict[str, Any], pack_id: str) -> dict[str, Any]:
    for pack in library.get("packs", []):
        if pack.get("id") == pack_id:
            return pack
    raise KeyError(f"Reference pack not found: {pack_id}")


def get_lesson(pack: dict[str, Any], lesson_id: str) -> dict[str, Any]:
    for lesson in pack.get("micro_lessons", []):
        if lesson.get("id") == lesson_id:
            return lesson
    raise KeyError(f"Lesson not found in pack {pack.get('id')}: {lesson_id}")


def build_run_context(
    *,
    experience_mode: str,
    source_strategy: str,
    reference_pack_id: str | None,
    lesson_id: str | None,
) -> dict[str, Any]:
    library = load_library()
    pack = get_pack(library, reference_pack_id) if reference_pack_id else None
    lesson = get_lesson(pack, lesson_id) if pack and lesson_id else None

    return {
        "experience_mode": experience_mode,
        "source_strategy": source_strategy,
        "library_version": library.get("version"),
        "source_policy": library.get("source_policy"),
        "selected_pack": pack,
        "selected_lesson": lesson,
    }


def build_reference_context(run_context: dict[str, Any] | None) -> str | None:
    if not run_context:
        return None

    pack = run_context.get("selected_pack")
    lesson = run_context.get("selected_lesson")
    source_policy = run_context.get("source_policy") or {}

    if not pack and not lesson:
        return None

    lines: list[str] = []
    lines.append(f"Experience mode: {run_context.get('experience_mode', 'learn')}")
    lines.append(f"Source strategy: {run_context.get('source_strategy', 'text-first')}")

    if source_policy:
        lines.append("Source governance:")
        lines.append(f"- authoritative_priority: {source_policy.get('authoritative_priority')}")
        lines.append(f"- youtube_policy: {source_policy.get('youtube_policy')}")
        lines.append(f"- export_policy: {source_policy.get('export_policy')}")

    if pack:
        lines.append(f"Trade pack: {pack.get('title')} ({pack.get('id')})")
        lines.append(f"Pack summary: {pack.get('summary')}")
        lines.append(f"Risk profile: {pack.get('risk_profile')}")
        lines.append("Pack backend enrichments:")
        for item in pack.get("backend_enrichment", []):
            lines.append(f"- {item}")

    if lesson:
        lines.append(f"Selected micro-lesson: {lesson.get('title')} ({lesson.get('id')})")
        lines.append(f"Scenario: {lesson.get('scenario')}")
        lines.append(f"Delivery target: {lesson.get('delivery_target')}")
        lines.append(f"Expert gate required: {lesson.get('expert_gate_required')}")
        lines.append("Overlay beats:")
        for beat in lesson.get("overlay_beats", []):
            lines.append(f"- {beat}")
        lines.append("Primary text sources:")
        for source in lesson.get("primary_text_sources", []):
            lines.append(f"- {source.get('publisher')}: {source.get('title')} ({source.get('url')})")
        lines.append("YouTube visual references:")
        for source in lesson.get("youtube_reference_videos", []):
            lines.append(f"- {source.get('title')} ({source.get('url')})")
        lines.append("Backend lookups:")
        for item in lesson.get("backend_enrichment", []):
            lines.append(f"- {item}")

    return "\n".join(lines)
