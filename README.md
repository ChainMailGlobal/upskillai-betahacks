# UpSkillAI Learn + Assist Scaffold

This repo started as a BetaHacks video scaffold and now moves toward the
broader UpSkillAI product:

- `Learn Mode`: text-first generation of byte-sized instructional clips with
  Seedance overlays
- `Assist Mode`: Spectacles or phone-guided field assistance with a remote
  expert, AI overlays, and backend code/permit lookups

The core media pipeline is still:

1. `Seed Speech ASR` transcribes a master-tradesperson recording.
2. `Seed 2.0 Pro` decomposes the transcript into structured procedure steps.
3. `Seedream 5.0` generates storyboard and AR-overlay keyframes.
4. `Seedance 2.0` animates those frames into short clips.
5. `Seed Speech TTS` generates the lesson voiceover.
6. `OmniHuman 1.5` renders the digital-twin talking head.
7. `ffmpeg` stitches the outputs into a submission-ready timeline.

The code defaults to `--dry-run` so it is usable immediately without live
credentials. Dry-run mode writes prompts, manifests, and stage outputs to
disk so the pipeline can be reviewed end to end before real API calls.

## Layout

- `catalog/reference_library.json`: trade packs and micro-lessons
- `reference_packs.py`: inspect packs and lessons from the terminal
- `build_kdemo.py`: generate a narrated demo animatic in minutes
- `docs/kdemo_quickstart.md`: fastest path to a pitchable MP4
- `docs/hackathon_screen_recording.md`: timed 3-minute judge walkthrough
- `record_judge_demo.ps1`: one-command local demo sequence for recording
- `docs/product_modes.md`: Learn Mode and Assist Mode architecture
- `docs/source_governance.md`: text-first source policy
- `orchestrator.py`: full DAG runner
- `render_shot.py`: reruns a single storyboard + animation shot
- `executors/`: BytePlus / Seed model adapters
- `pipeline/`: stage logic and artifact persistence
- `runs/`: generated manifests and outputs

## Quick Start

```powershell
cd c:\OpenClawLens\Assets\upskillai_betahacks
python reference_packs.py
python reference_packs.py --pack mini_split_field_service
python build_kdemo.py --run-name kdemo_fast
python orchestrator.py --run-name demo --dry-run
python render_shot.py --run-name demo --step 1 --dry-run
python orchestrator.py --run-name hvac_demo --dry-run --reference-pack mini_split_field_service --lesson-id mini_split_filter_cleaning
python orchestrator.py --run-name live_smoke --input-video .\inputs\master_recording.mp4 --stop-after transcribe
```

The first command creates a resumable run under `runs/demo/`.

## Product Modes

- `--mode learn`: generate short educational overlays and explainer clips
- `--mode assist`: prepare a run for remote-expert and backend-enriched field support

## Source Strategy

The default is `--source-strategy text-first`.

That means:

- manufacturer manuals and other text sources drive the script
- YouTube videos are used for visual reference only
- generated clips should be new renders, not reused third-party footage

See [docs/source_governance.md](docs/source_governance.md).

## Environment

Set these for live execution:

```powershell
$env:BYTEPLUS_API_KEY="..."
$env:BYTEPLUS_BASE_URL="https://ark.ap-southeast.bytepluses.com/api/v3"
$env:MISTRAL_API_KEY="..."
```

You can also start from `.env.example` and map those values into your shell or runner.

Optional overrides:

```powershell
$env:SEED_CHAT_MODEL="dola-seed-2-0-pro"
$env:SEED_IMAGE_MODEL="seedream-5-0-260128"
$env:SEED_VIDEO_MODEL="dreamina-seedance-2-0-fast-260128"
$env:SEED_ASR_MODEL="seed-asr-2-0"
$env:SEED_TTS_MODEL="seed-tts-2-0"
$env:OMNIHUMAN_MODEL="bytedance-omnihuman-v1-5"
$env:SEED_VIDEO_CREATE_PATH="/videos/create_task"
$env:SEED_VIDEO_RETRIEVE_PATH="/videos/retrieve_task"
$env:SEED_TTS_PATH="/audio/speech"
$env:OMNIHUMAN_CREATE_PATH="/omnihuman/create_task"
$env:OMNIHUMAN_RETRIEVE_PATH="/omnihuman/retrieve_task"
$env:SEED_VOICE_ID="optional-cloned-voice-id"
$env:MISTRAL_TTS_MODEL="voxtral-mini-tts-2603"
$env:MISTRAL_API_BASE="https://api.mistral.ai"
$env:MISTRAL_VOICE_ID="optional-saved-voice-id"
```

For the fast demo builder, `build_kdemo.py` supports:

- `--voice auto`: prefer Mistral when configured, else try Windows TTS
- `--voice mistral`: force Voxtral TTS via `MISTRAL_API_KEY`
- `--mistral-voice-id`: use a saved Mistral voice for consistency
- `--mistral-ref-audio`: use a one-off voice sample such as `inputs/stan_voice_sample.wav`

## Expected Inputs

Drop source assets into `inputs/` or pass explicit paths:

- `inputs/master_recording.mp3`
- `inputs/master_recording.mp4` or `inputs/master_recording.mov`
- `inputs/stan_portrait.jpg`
- `inputs/stan_voice_sample.wav` (optional)

If you only have video, that is fine. The pipeline will extract mono WAV for ASR
with local `ffmpeg` before calling Seed Speech.

Examples:

```powershell
python orchestrator.py `
  --run-name breaker_panel `
  --mode learn `
  --reference-pack electrical_field_basics `
  --lesson-id electrical_panel_orientation `
  --input-video .\inputs\master_recording.mp4 `
  --stan-portrait .\inputs\stan_portrait.jpg
```

## Notes

- Live HTTP paths are configurable because BytePlus video, TTS, and OmniHuman
  endpoints vary by account and API surface.
- Every stage persists JSON to disk so retries can resume without rerunning
  successful upstream work.
- `render_shot.py` exists specifically for the single-shot recovery flow the
  PDF calls out in its risk register.
- The current repo is still a scaffold: realtime expert video, OEM document
  retrieval, jurisdiction adapters, and asset re-hosting are still separate
  implementation tasks.
