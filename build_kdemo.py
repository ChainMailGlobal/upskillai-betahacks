from __future__ import annotations

import argparse
import base64
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import urllib.error
import urllib.request
import wave

from catalog import get_lesson, get_pack, load_library


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a fast demo video package and text animatic.")
    parser.add_argument("--run-name", required=True, help="Directory name under runs/.")
    parser.add_argument(
        "--hero-pack",
        default="mini_split_field_service",
        help="Primary trade pack for the hero section.",
    )
    parser.add_argument(
        "--hero-lesson",
        default="mini_split_fault_code_triage",
        help="Primary lesson id inside the hero pack.",
    )
    parser.add_argument(
        "--voice",
        choices=["auto", "mistral", "windows", "none"],
        default="auto",
        help="Narration engine for the demo animatic.",
    )
    parser.add_argument(
        "--mistral-voice-id",
        help="Saved Mistral voice id. Overrides MISTRAL_VOICE_ID.",
    )
    parser.add_argument(
        "--mistral-ref-audio",
        help="Path to a short reference audio clip for one-off Mistral voice cloning.",
    )
    parser.add_argument(
        "--mistral-model",
        default=os.getenv("MISTRAL_TTS_MODEL", "voxtral-mini-tts-2603"),
        help="Mistral TTS model id.",
    )
    parser.add_argument(
        "--mistral-api-base",
        default=os.getenv("MISTRAL_API_BASE", "https://api.mistral.ai"),
        help="Base URL for the Mistral API.",
    )
    parser.add_argument(
        "--resolution",
        default="1920x1080",
        help="Output resolution as WIDTHxHEIGHT.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent
    run_dir = project_root / "runs" / args.run_name
    output_dir = run_dir / "kdemo"
    slides_dir = output_dir / "slides"
    audio_dir = output_dir / "audio"
    video_dir = output_dir / "segments"
    inputs_dir = project_root / "inputs"
    for directory in (output_dir, slides_dir, audio_dir, video_dir):
        directory.mkdir(parents=True, exist_ok=True)

    library = load_library()
    hero_pack = get_pack(library, args.hero_pack)
    hero_lesson = get_lesson(hero_pack, args.hero_lesson)
    slides = build_slides(library, hero_pack, hero_lesson)

    plan_path = output_dir / "kdemo_plan.json"
    script_path = output_dir / "narration_script.txt"
    srt_path = output_dir / "captions.srt"
    plan_path.write_text(json.dumps({"slides": slides}, indent=2), encoding="utf-8")
    script_path.write_text(build_script_text(slides), encoding="utf-8")

    font_regular = Path(r"C:\Windows\Fonts\arial.ttf")
    font_bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to build the demo video.")
    ffprobe = shutil.which("ffprobe")

    resolution = parse_resolution(args.resolution)
    mistral_ref_audio = resolve_mistral_ref_audio(args.mistral_ref_audio, inputs_dir)
    voice_mode = resolve_voice_mode(
        requested_mode=args.voice,
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        mistral_voice_id=args.mistral_voice_id or os.getenv("MISTRAL_VOICE_ID"),
        mistral_ref_audio=mistral_ref_audio,
    )
    slide_segments: list[Path] = []
    caption_entries: list[dict[str, str]] = []
    current_start = 0.0
    narrated_segments = 0

    for index, slide in enumerate(slides, start=1):
        title_file = slides_dir / f"slide_{index:02d}_title.txt"
        body_file = slides_dir / f"slide_{index:02d}_body.txt"
        footer_file = slides_dir / f"slide_{index:02d}_footer.txt"
        title_file.write_text(slide["title"], encoding="utf-8")
        body_file.write_text("\n".join(slide["body"]), encoding="utf-8")
        footer_file.write_text(slide["footer"], encoding="utf-8")

        audio_path = None
        audio_duration = 0.0
        if voice_mode == "mistral":
            audio_path = audio_dir / f"slide_{index:02d}.mp3"
            if synthesize_mistral_tts(
                text=slide["narration"],
                output_path=audio_path,
                api_base=args.mistral_api_base,
                api_key=os.getenv("MISTRAL_API_KEY"),
                model=args.mistral_model,
                voice_id=args.mistral_voice_id or os.getenv("MISTRAL_VOICE_ID"),
                ref_audio_path=mistral_ref_audio,
            ):
                audio_duration = probe_media_duration(audio_path, ffprobe)
            else:
                audio_path = None
                audio_duration = 0.0
        elif voice_mode == "windows":
            audio_path = audio_dir / f"slide_{index:02d}.wav"
            if synthesize_windows_tts(slide["narration"], audio_path):
                audio_duration = probe_media_duration(audio_path, ffprobe)
            else:
                audio_path = None
                audio_duration = 0.0

        duration = max(slide["min_duration_sec"], audio_duration + 0.6 if audio_duration else 0.0)
        segment_video = video_dir / f"slide_{index:02d}_video.mp4"
        render_slide_video(
            ffmpeg=ffmpeg,
            output_path=segment_video,
            duration=duration,
            resolution=resolution,
            palette=slide["palette"],
            title_file=title_file,
            body_file=body_file,
            footer_file=footer_file,
            font_regular=font_regular,
            font_bold=font_bold,
        )

        final_segment = video_dir / f"slide_{index:02d}.mp4"
        if audio_path and audio_path.exists():
            narrated_segments += 1
            mux_slide_audio(
                ffmpeg=ffmpeg,
                video_path=segment_video,
                audio_path=audio_path,
                output_path=final_segment,
                duration=duration,
            )
        else:
            final_segment = segment_video

        slide_segments.append(final_segment)
        caption_entries.append(
            {
                "index": str(index),
                "start": seconds_to_srt(current_start),
                "end": seconds_to_srt(current_start + duration),
                "text": slide["narration"],
            }
        )
        current_start += duration

    srt_path.write_text(build_srt(caption_entries), encoding="utf-8")

    concat_path = output_dir / "segments.txt"
    concat_path.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in slide_segments),
        encoding="utf-8",
    )
    final_video = output_dir / "kdemo_animatic.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            str(final_video),
        ],
        check=True,
    )

    if voice_mode != "none" and narrated_segments == 0:
        print(
            "Warning: no narration audio was generated. "
            "The MP4 was built as a silent animatic. "
            "Configure MISTRAL_API_KEY to use Voxtral narration. "
            "Add MISTRAL_VOICE_ID or inputs/stan_voice_sample.* if you want a consistent cloned voice."
        )

    print(f"Demo plan: {plan_path}")
    print(f"Narration script: {script_path}")
    print(f"Captions: {srt_path}")
    print(f"Video: {final_video}")


def build_slides(library: dict, hero_pack: dict, hero_lesson: dict) -> list[dict]:
    all_pack_titles = [pack["title"] for pack in library.get("packs", [])]
    hero_sources = hero_lesson.get("primary_text_sources", [])[:2]
    hero_youtube = hero_lesson.get("youtube_reference_videos", [])[:1]

    text_source_line = " + ".join(source["publisher"] for source in hero_sources) or "manufacturer text sources"
    youtube_line = hero_youtube[0]["publisher"] if hero_youtube else "YouTube visual reference"

    slides = [
        {
            "title": "UpSkillAI",
            "body": [
                "Learn Mode + Assist Mode for skilled trades",
                "Text-first AR lesson generation with Seedance-ready prompts",
                "Hands-free field support with Spectacles or phone",
            ],
            "footer": "Skilled knowledge capture -> AR overlays -> remote expert assist",
            "narration": (
                "This is UpSkillAI. We turn trusted trade knowledge into byte-sized AR lessons, "
                "and we extend the same system into live field assistance for workers using Spectacles or a phone."
            ),
            "palette": {"bg": "0x0F172A", "accent": "0x22C55E"},
            "min_duration_sec": 7.5,
        },
        {
            "title": "Five Trade Packs",
            "body": [
                "Electrical, mini-split HVAC, painting, windows, and auto maintenance",
                "Each pack includes micro-lessons, risk gates, overlay beats, and backend lookups",
                "Authority comes from manuals, owner docs, safety sources, and trusted text references",
            ],
            "footer": "Coverage: " + ", ".join(all_pack_titles),
            "narration": (
                "The content system already covers five trade packs: electrical, mini-split HVAC, painting, "
                "window replacement, and auto maintenance. Each pack is structured as reusable micro-lessons, "
                "not one-off demo prompts."
            ),
            "palette": {"bg": "0x111827", "accent": "0x38BDF8"},
            "min_duration_sec": 7.5,
        },
        {
            "title": hero_lesson["title"],
            "body": [
                hero_lesson["scenario"],
                f"Text authority: {text_source_line}",
                f"Visual blocking only: {youtube_line}",
            ],
            "footer": f"Hero pack: {hero_pack['title']}",
            "narration": (
                f"Our hero example is {hero_lesson['title'].lower()}. "
                f"We generate the lesson from text-based sources like {text_source_line}, "
                f"while using {youtube_line} only to inform visual blocking and spatial rhythm."
            ),
            "palette": {"bg": "0x082F49", "accent": "0xF59E0B"},
            "min_duration_sec": 8.0,
        },
        {
            "title": "AR Overlay Beats",
            "body": hero_lesson["overlay_beats"][:4],
            "footer": "Seedream keyframes -> Seedance motion -> AR training clip",
            "narration": (
                "For each micro-lesson we store the overlay beats directly. "
                + " ".join(
                    f"Beat {idx}: {beat}."
                    for idx, beat in enumerate(hero_lesson["overlay_beats"][:4], start=1)
                )
            ),
            "palette": {"bg": "0x052E16", "accent": "0xA3E635"},
            "min_duration_sec": 9.0,
        },
        {
            "title": "Expert-Gated Workflows",
            "body": [
                "Electrical panel interior work, refrigerant or line-set service, and brakes stay gated",
                "Low-risk lessons stay DIY-friendly: painting prep, filter cleaning, window measuring, tire pressure",
                "Every lesson carries risk class, expert gate, and backend enrichment metadata",
            ],
            "footer": "Safety model: AI assists. Experts decide.",
            "narration": (
                "We separate low-risk homeowner lessons from expert-gated workflows. "
                "Electrical panel work, refrigerant service, and brake jobs stay gated, while painting prep, "
                "filter cleaning, window measuring, and tire pressure checks remain lightweight and teachable."
            ),
            "palette": {"bg": "0x3F1D2E", "accent": "0xFB7185"},
            "min_duration_sec": 8.0,
        },
        {
            "title": "Assist Mode Live Session",
            "body": [
                "Onsite worker wears Spectacles or uses a phone",
                "Remote expert appears in a picture-in-picture tile",
                "AI overlays anchor to the equipment while the backend looks up manuals, parts, permits, and codes",
            ],
            "footer": "Spectacles/Phone + Expert + AI + OEM/Permit Backend",
            "narration": (
                "Assist Mode is the live version of the same system. "
                "The onsite worker streams from Spectacles or a phone, a remote expert joins in picture-in-picture, "
                "and the AI layers visual guidance on top of the actual equipment while the backend pulls manuals, "
                "fault codes, permit notes, and inspection checklists."
            ),
            "palette": {"bg": "0x172554", "accent": "0x60A5FA"},
            "min_duration_sec": 9.5,
        },
        {
            "title": "One-Hour Demo Path",
            "body": [
                "Today: use the text animatic as the kdemo base",
                "Next: replace text cards with Seedance clips from the same pack metadata",
                "End state: lessons and live assist run on the same trade graph",
            ],
            "footer": "Use now: narrated animatic. Upgrade next: Seedance lesson clips.",
            "narration": (
                "For this hour, the fastest demo is a narrated animatic built from the same trade graph the product will use in production. "
                "Next, the text cards get swapped for Seedance lesson clips and live Assist Mode UI, without changing the lesson model underneath."
            ),
            "palette": {"bg": "0x1F2937", "accent": "0xF97316"},
            "min_duration_sec": 8.5,
        },
    ]
    return slides


def build_script_text(slides: list[dict]) -> str:
    lines = []
    for index, slide in enumerate(slides, start=1):
        lines.append(f"Slide {index}: {slide['title']}")
        lines.append(slide["narration"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def parse_resolution(value: str) -> tuple[int, int]:
    width_str, height_str = value.lower().split("x", 1)
    return int(width_str), int(height_str)


def resolve_voice_mode(
    *,
    requested_mode: str,
    mistral_api_key: str | None,
    mistral_voice_id: str | None,
    mistral_ref_audio: Path | None,
) -> str:
    if requested_mode == "auto":
        if mistral_api_key:
            return "mistral"
        return "windows"
    if requested_mode == "mistral" and not mistral_api_key:
        raise RuntimeError("MISTRAL_API_KEY is required when --voice mistral is selected.")
    return requested_mode


def resolve_mistral_ref_audio(explicit_path: str | None, inputs_dir: Path) -> Path | None:
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
        if not path.exists():
            raise RuntimeError(f"Mistral reference audio not found: {path}")
        return path
    for filename in (
        "stan_voice_sample.wav",
        "stan_voice_sample.mp3",
        "stan_voice_sample.m4a",
        "stan_voice_sample.flac",
        "stan_voice_sample.opus",
    ):
        candidate = inputs_dir / filename
        if candidate.exists():
            return candidate.resolve()
    return None


def synthesize_mistral_tts(
    *,
    text: str,
    output_path: Path,
    api_base: str,
    api_key: str | None,
    model: str,
    voice_id: str | None,
    ref_audio_path: Path | None,
) -> bool:
    if not api_key:
        return False

    payload: dict[str, object] = {
        "model": model,
        "input": normalize_tts_text(text),
        "response_format": "mp3",
    }
    if voice_id:
        payload["voice_id"] = voice_id
    elif ref_audio_path:
        payload["ref_audio"] = base64.b64encode(ref_audio_path.read_bytes()).decode("ascii")

    request = urllib.request.Request(
        url=api_base.rstrip("/") + "/v1/audio/speech",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Mistral TTS request failed: {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Mistral TTS request failed: {exc.reason}") from exc

    audio_data = body.get("audio_data")
    if not isinstance(audio_data, str) or not audio_data:
        raise RuntimeError("Mistral TTS response did not include audio_data.")
    output_path.write_bytes(base64.b64decode(audio_data))
    return output_path.exists() and output_path.stat().st_size > 0


def synthesize_windows_tts(text: str, output_path: Path) -> bool:
    safe_text = text.replace("'", "''")
    safe_output = str(output_path).replace("'", "''")
    command = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 0; "
        f"$s.SetOutputToWaveFile('{safe_output}'); "
        f"$s.Speak('{safe_text}'); "
        "$s.Dispose();"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and output_path.exists()


def probe_media_duration(path: Path, ffprobe: str | None) -> float:
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as handle:
            frames = handle.getnframes()
            framerate = handle.getframerate()
        return frames / float(framerate)
    if not ffprobe:
        raise RuntimeError("ffprobe is required to measure non-WAV audio duration.")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def normalize_tts_text(text: str) -> str:
    normalized = " ".join(text.replace("\n", " ").split())
    return normalized.replace("&", "and")


def render_slide_video(
    *,
    ffmpeg: str,
    output_path: Path,
    duration: float,
    resolution: tuple[int, int],
    palette: dict[str, str],
    title_file: Path,
    body_file: Path,
    footer_file: Path,
    font_regular: Path,
    font_bold: Path,
) -> None:
    width, height = resolution
    vf = ",".join(
        [
            f"drawbox=x=110:y=100:w={width - 220}:h=10:color={palette['accent']}:t=fill",
            (
                "drawtext="
                f"fontfile='{ffmpeg_path(font_bold)}':"
                f"textfile='{ffmpeg_path(title_file)}':"
                "fontcolor=white:fontsize=74:line_spacing=10:"
                "x=120:y=155"
            ),
            (
                "drawtext="
                f"fontfile='{ffmpeg_path(font_regular)}':"
                f"textfile='{ffmpeg_path(body_file)}':"
                "fontcolor=white:fontsize=36:line_spacing=18:"
                "x=120:y=330"
            ),
            (
                "drawtext="
                f"fontfile='{ffmpeg_path(font_regular)}':"
                f"textfile='{ffmpeg_path(footer_file)}':"
                f"fontcolor={palette['accent']}:fontsize=28:line_spacing=12:"
                f"x=120:y={height - 120}"
            ),
        ]
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={palette['bg']}:s={width}x{height}:d={duration:.2f}",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ],
        check=True,
    )


def mux_slide_audio(
    *,
    ffmpeg: str,
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    duration: float,
) -> None:
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-filter:a",
            "apad",
            "-t",
            f"{duration:.2f}",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            str(output_path),
        ],
        check=True,
    )


def build_srt(entries: list[dict[str, str]]) -> str:
    blocks = []
    for entry in entries:
        blocks.append(f"{entry['index']}\n{entry['start']} --> {entry['end']}\n{entry['text']}\n")
    return "\n".join(blocks)


def seconds_to_srt(value: float) -> str:
    total_ms = int(math.floor(value * 1000))
    hours, rem = divmod(total_ms, 3600 * 1000)
    minutes, rem = divmod(rem, 60 * 1000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def ffmpeg_path(path: Path) -> str:
    normalized = path.resolve().as_posix()
    return normalized.replace(":", r"\:")


if __name__ == "__main__":
    main()
