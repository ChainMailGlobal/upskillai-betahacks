# 3-Minute Screen Recording Runbook

This is the fastest judge-friendly walkthrough for the BetaHacks submission.

Target length: `2:45` to `3:00`

Recording target:

- one continuous screen recording
- terminal + editor/browser only
- upload to unlisted YouTube or public Google Drive

## What To Show

Show three things only:

1. the GitHub repo exists and is structured like a real product
2. the trade knowledge system is already modeled into reusable packs and micro-lessons
3. the pipeline can generate a concrete lesson/demo path right now

Do not try to explain every file.

## Recording Order

### 0:00 to 0:20

Open:

- GitHub repo: `https://github.com/ChainMailGlobal/upskillai-betahacks`
- local repo README

Say:

`This is UpSkillAI. We turn trusted trade instructions into AR micro-lessons and extend the same system into live remote expert assistance for workers using Spectacles or a phone.`

### 0:20 to 0:50

In the repo, show:

- `catalog/reference_library.json`
- `docs/product_modes.md`
- `build_kdemo.py`

Say:

`The project is structured around reusable trade packs, not a one-off video. Each lesson has authoritative text sources, YouTube used only for visual blocking, overlay beats, backend enrichments, and an expert gate when the work is high risk.`

### 0:50 to 1:20

Run:

```powershell
python reference_packs.py
python reference_packs.py --pack mini_split_field_service
```

Say:

`Right now the library covers electrical, mini-split HVAC, painting, windows, and auto maintenance. Here I’m opening the mini-split pack, which already contains multiple field scenarios with risk gating and backend lookup metadata.`

### 1:20 to 1:55

Run:

```powershell
python orchestrator.py --run-name judge_demo --dry-run --mode learn --reference-pack mini_split_field_service --lesson-id mini_split_fault_code_triage --stop-after decompose
```

Then open:

- `runs/judge_demo/run_context.json`
- `runs/judge_demo/stages/decompose.json`

Say:

`This is the lesson generation path. The run context locks the product mode, source strategy, selected trade pack, and selected lesson. The decompose stage converts that into structured procedural steps that can drive storyboard prompts, AR overlays, narration, and expert escalation logic.`

### 1:55 to 2:30

Run:

```powershell
python build_kdemo.py --run-name judge_demo --voice auto
```

If Mistral is not configured, use:

```powershell
python build_kdemo.py --run-name judge_demo --voice none
```

Then show:

- `runs/judge_demo/kdemo/kdemo_plan.json`
- `runs/judge_demo/kdemo/kdemo_animatic.mp4`

Say:

`For the hackathon, the fastest proof is a generated demo package. It creates a script, captions, and a pitchable animatic from the same structured trade graph, and when Mistral is configured it can narrate it through Voxtral TTS.`

### 2:30 to 3:00

Close on:

- `docs/product_modes.md`
- `README.md`

Say:

`The real business is bigger than a demo video. Learn Mode generates byte-sized AR training clips from trusted text sources, and Assist Mode supports live remote expert help with Spectacles or phone, AI overlays, and backend code, permit, and OEM lookups.`

## Exact Command Block

Run this in `c:\OpenClawLens\Assets\upskillai_betahacks`:

```powershell
python reference_packs.py
python reference_packs.py --pack mini_split_field_service
python orchestrator.py --run-name judge_demo --dry-run --mode learn --reference-pack mini_split_field_service --lesson-id mini_split_fault_code_triage --stop-after decompose
python build_kdemo.py --run-name judge_demo --voice auto
```

Fallback if narration is not configured:

```powershell
python build_kdemo.py --run-name judge_demo --voice none
```

## Recording Tips

- Keep your editor zoomed in. Judges will watch this quickly.
- Use one terminal window only.
- Do not scroll fast through JSON. Open the file and pause on the high-signal fields.
- If the animatic is silent, say that narration is wired for Voxtral TTS and the builder falls back cleanly.
- Do not mention unfinished features unless you immediately connect them to the business direction.
