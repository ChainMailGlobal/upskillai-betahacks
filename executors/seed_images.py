from __future__ import annotations

from typing import Any

from .modelark import ModelArkClient


def generate_image(
    client: ModelArkClient,
    model: str,
    prompt: str,
    size: str = "2048x1536",
) -> dict[str, Any]:
    response = client.post_json(
        "/images/generations",
        {
            "model": model,
            "prompt": prompt,
            "size": size,
        },
    )
    data = response.get("data") or []
    if not data:
        raise RuntimeError("Seedream response did not include image data.")
    first = data[0]
    return {
        "url": first.get("url"),
        "revised_prompt": first.get("revised_prompt"),
        "raw": response,
    }
