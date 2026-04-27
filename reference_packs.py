from __future__ import annotations

import argparse
import json

from catalog import get_lesson, get_pack, load_library


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect trade reference packs and lessons.")
    parser.add_argument("--pack", help="Reference pack id.")
    parser.add_argument("--lesson-id", help="Lesson id inside the selected pack.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    library = load_library()

    if not args.pack:
        summary = [
            {
                "id": pack["id"],
                "title": pack["title"],
                "risk_profile": pack["risk_profile"],
                "lesson_count": len(pack.get("micro_lessons", [])),
            }
            for pack in library.get("packs", [])
        ]
        print(json.dumps(summary, indent=2))
        return

    pack = get_pack(library, args.pack)
    if not args.lesson_id:
        payload = {
            "id": pack["id"],
            "title": pack["title"],
            "summary": pack["summary"],
            "risk_profile": pack["risk_profile"],
            "backend_enrichment": pack["backend_enrichment"],
            "micro_lessons": [
                {
                    "id": lesson["id"],
                    "title": lesson["title"],
                    "delivery_target": lesson["delivery_target"],
                    "expert_gate_required": lesson["expert_gate_required"],
                }
                for lesson in pack.get("micro_lessons", [])
            ],
        }
        print(json.dumps(payload, indent=2))
        return

    lesson = get_lesson(pack, args.lesson_id)
    print(json.dumps(lesson, indent=2))


if __name__ == "__main__":
    main()
