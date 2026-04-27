# BytePlus 2-Minute Submission

Use this path for the BytePlus Seed-only video competition.

Important:

- Do not rely on `build_kdemo.py` as the core artifact for this track.
- `build_kdemo.py` is still useful for pitch rehearsal, but it is not the BytePlus-only proof.
- For this submission, the hero evidence should be live outputs from the `storyboard`, `animate`, `voice`, and optionally `digital_twin` stages.

## Rule Fit

Current repo mapping:

- `Seed 2.0`: transcript decomposition and prompt generation
- `Seedream 5.0`: storyboard / keyframe generation
- `Seedance 2.0`: animated clip generation
- `Seed Speech`: ASR + voice synthesis
- `OmniHuman`: digital human explainer

## Required Local Inputs

Put these into `inputs/` or pass them explicitly:

- `master_recording.mp4` or `master_recording.mp3`
- `stan_portrait.jpg` if you want OmniHuman in the run

## Fastest Live Run

```powershell
cd c:\OpenClawLens\Assets\upskillai_betahacks
$env:BYTEPLUS_API_KEY="your-real-byteplus-key"
python orchestrator.py --run-name byteplus_demo --mode assist --reference-pack mini_split_field_service --lesson-id mini_split_fault_code_triage --input-video .\inputs\master_recording.mp4 --stop-after animate
python prepare_byteplus_submission.py --run-name byteplus_demo
```

If you also have a portrait ready for the digital human:

```powershell
python orchestrator.py --run-name byteplus_demo --mode assist --reference-pack mini_split_field_service --lesson-id mini_split_fault_code_triage --input-video .\inputs\master_recording.mp4 --stan-portrait .\inputs\stan_portrait.jpg --stop-after digital_twin
python prepare_byteplus_submission.py --run-name byteplus_demo
```

## What To Show In The 2-Minute Video

### 0:00-1:00 Live Demo

Lead with generated outputs, not architecture.

Show in this order:

- `runs/byteplus_demo/outputs/clips/`
- `runs/byteplus_demo/outputs/storyboards/`
- `runs/byteplus_demo/outputs/voice/voiceover.mp3` if present
- `runs/byteplus_demo/outputs/omnihuman/stan_twin.mp4` if present

Say:

`UpSkillAI uses BytePlus Seed models to turn trusted trade instructions into short AR-style field lessons and remote-assist flows for workers using Spectacles or a phone.`

### 1:00-1:30 Technical Architecture

Show:

- `runs/byteplus_demo/manifest.json`
- `runs/byteplus_demo/stages/run_context.json`
- `runs/byteplus_demo/stages/decompose.json`
- `runs/byteplus_demo/stages/storyboard.json`
- `runs/byteplus_demo/stages/animate.json`

Say:

`Seed 2.0 structures the lesson and prompt set, Seedream 5.0 generates keyframes, Seedance 2.0 turns those into video clips, Seed Speech handles voice, and OmniHuman can generate the digital presenter.`

### 1:30-2:00 Vision

Show:

- `docs/product_modes.md`
- `README.md`

Say:

`Beyond the hackathon, the same lesson graph powers live Assist Mode: hands-free Spectacles capture, remote expert escalation, AI overlays on real equipment, and backend lookups for OEM manuals, codes, permits, and checklists.`

## Compliance Check

After a run, inspect:

- `runs/byteplus_demo/submission/byteplus_submission_summary.json`
- `runs/byteplus_demo/submission/byteplus_talk_track.md`

The summary marks the run `ready` only if a live `animate` stage completed without dry-run markers.
