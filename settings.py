from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _maybe_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser().resolve()


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path.resolve()
    return None


def _resolve_input_path(
    explicit: str | None,
    inputs_dir: Path,
    candidates: list[str],
    default_name: str,
) -> Path:
    explicit_path = _maybe_path(explicit)
    if explicit_path is not None:
        return explicit_path

    existing = _first_existing([inputs_dir / candidate for candidate in candidates])
    if existing is not None:
        return existing

    return (inputs_dir / default_name).resolve()


@dataclass(frozen=True)
class Settings:
    project_root: Path
    run_name: str
    dry_run: bool
    experience_mode: str
    source_strategy: str
    reference_pack_id: str | None
    lesson_id: str | None
    input_audio: Path | None
    input_video: Path | None
    stan_portrait: Path | None
    stan_voice_sample: Path | None
    byteplus_api_key: str | None
    byteplus_base_url: str
    request_timeout_sec: float
    poll_interval_sec: float
    asr_model: str
    chat_model: str
    image_model: str
    video_model: str
    tts_model: str
    omnihuman_model: str
    seed_video_create_path: str
    seed_video_retrieve_path: str
    seed_tts_path: str
    omnihuman_create_path: str
    omnihuman_retrieve_path: str
    seed_voice_id: str | None

    @property
    def inputs_dir(self) -> Path:
        return self.project_root / "inputs"

    @property
    def runs_dir(self) -> Path:
        return self.project_root / "runs"

    @property
    def run_dir(self) -> Path:
        return self.runs_dir / self.run_name

    @classmethod
    def from_args(cls, args: object) -> "Settings":
        project_root = Path(__file__).resolve().parent
        inputs_dir = project_root / "inputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        input_audio = getattr(args, "input_audio", None)
        input_video = getattr(args, "input_video", None)
        stan_portrait = getattr(args, "stan_portrait", None)
        stan_voice_sample = getattr(args, "stan_voice_sample", None)

        return cls(
            project_root=project_root,
            run_name=getattr(args, "run_name"),
            dry_run=bool(getattr(args, "dry_run")) or env_bool("UPSKILLAI_DRY_RUN", False),
            experience_mode=str(getattr(args, "mode", "learn")),
            source_strategy=str(getattr(args, "source_strategy", "text-first")),
            reference_pack_id=getattr(args, "reference_pack", None),
            lesson_id=getattr(args, "lesson_id", None),
            input_audio=_resolve_input_path(
                input_audio,
                inputs_dir,
                [
                    "master_recording.mp3",
                    "master_recording.wav",
                    "master_recording.m4a",
                    "master_recording.aac",
                    "master_recording.flac",
                ],
                "master_recording.mp3",
            ),
            input_video=_resolve_input_path(
                input_video,
                inputs_dir,
                [
                    "master_recording.mp4",
                    "master_recording.mov",
                    "master_recording.mkv",
                    "master_recording.webm",
                ],
                "master_recording.mp4",
            ),
            stan_portrait=_resolve_input_path(
                stan_portrait,
                inputs_dir,
                [
                    "stan_portrait.jpg",
                    "stan_portrait.jpeg",
                    "stan_portrait.png",
                    "stan_portrait.webp",
                ],
                "stan_portrait.jpg",
            ),
            stan_voice_sample=_resolve_input_path(
                stan_voice_sample,
                inputs_dir,
                [
                    "stan_voice_sample.wav",
                    "stan_voice_sample.mp3",
                    "stan_voice_sample.m4a",
                ],
                "stan_voice_sample.wav",
            ),
            byteplus_api_key=os.getenv("BYTEPLUS_API_KEY"),
            byteplus_base_url=os.getenv(
                "BYTEPLUS_BASE_URL",
                "https://ark.ap-southeast.bytepluses.com/api/v3",
            ),
            request_timeout_sec=float(os.getenv("BYTEPLUS_REQUEST_TIMEOUT_SEC", "120")),
            poll_interval_sec=float(os.getenv("BYTEPLUS_POLL_INTERVAL_SEC", "5")),
            asr_model=os.getenv("SEED_ASR_MODEL", "seed-asr-2-0"),
            chat_model=os.getenv("SEED_CHAT_MODEL", "dola-seed-2-0-pro"),
            image_model=os.getenv("SEED_IMAGE_MODEL", "seedream-5-0-260128"),
            video_model=os.getenv("SEED_VIDEO_MODEL", "dreamina-seedance-2-0-fast-260128"),
            tts_model=os.getenv("SEED_TTS_MODEL", "seed-tts-2-0"),
            omnihuman_model=os.getenv("OMNIHUMAN_MODEL", "bytedance-omnihuman-v1-5"),
            seed_video_create_path=os.getenv("SEED_VIDEO_CREATE_PATH", "/videos/create_task"),
            seed_video_retrieve_path=os.getenv("SEED_VIDEO_RETRIEVE_PATH", "/videos/retrieve_task"),
            seed_tts_path=os.getenv("SEED_TTS_PATH", "/audio/speech"),
            omnihuman_create_path=os.getenv("OMNIHUMAN_CREATE_PATH", "/omnihuman/create_task"),
            omnihuman_retrieve_path=os.getenv("OMNIHUMAN_RETRIEVE_PATH", "/omnihuman/retrieve_task"),
            seed_voice_id=os.getenv("SEED_VOICE_ID"),
        )

    def validate_for_live_mode(self) -> None:
        if self.dry_run:
            return
        if not self.byteplus_api_key:
            raise RuntimeError("BYTEPLUS_API_KEY is required when --dry-run is not set.")
        if self.input_audio and self.input_audio.exists():
            return
        if self.input_video and self.input_video.exists():
            if not shutil.which("ffmpeg"):
                raise RuntimeError(
                    "An input video was found but ffmpeg is not installed, so audio cannot be "
                    f"extracted automatically. Video path: {self.input_video}"
                )
            return
        if not self.input_audio or not self.input_audio.exists():
            raise RuntimeError(
                "A real input audio or video file is required for live mode. "
                f"Expected one of the default files under {self.inputs_dir} "
                f"(audio target: {self.input_audio}, video target: {self.input_video}) "
                "or pass --input-audio <path> / --input-video <path>. "
                "Use --dry-run if you only want to validate the scaffold."
            )
