# Learn Mode + Assist Mode

This repo now targets two related product modes rather than a single hackathon
render script.

## Learn Mode

Goal: turn authoritative text instructions into short, animated AR teaching
clips with Seedance and overlay-friendly keyframes.

Flow:

1. Select a trade reference pack and micro-lesson.
2. Use manufacturer manuals, owner manuals, and text-based trade articles as
   the source of truth for sequence, safety language, and tool requirements.
3. Use YouTube videos only as visual blocking references for:
   - camera framing
   - hand placement rhythm
   - before/after scene structure
   - common spatial anchor positions
4. Generate:
   - step JSON
   - storyboard prompts
   - motion prompts
   - voiceover
   - optional digital twin explainer
5. Export byte-sized lesson clips for web, phone, or Spectacles preview.

Good targets:

- painting prep
- mini-split filter cleaning
- window measurement
- tire pressure check
- breaker panel orientation with heavy safety gating

## Assist Mode

Goal: help an onsite worker using Spectacles or a phone while a remote expert
and AI operate on the same job.

Core UX:

- main live POV from Spectacles or phone camera
- picture-in-picture remote expert tile
- AI overlay layer on the real equipment
- backend card stack for:
  - codes
  - permitting
  - OEM manual excerpts
  - fault codes
  - checklist state

Suggested voice and UI actions:

- `freeze frame`
- `label disconnect`
- `show drain slope`
- `show next step`
- `look up model`
- `check permit requirement`
- `call expert`

## Recommended System Split

### Onsite worker

- Spectacles Lens for hands-free AR
- phone fallback app using Camera Kit or standard mobile camera UI
- local capture of photos, short clips, and notes

### Remote expert console

- web app with live video feed
- annotation tools
- source pane for manuals, permit notes, and AI summary
- timeline of captured frames and decisions

### Backend

- realtime session service
- media storage
- OCR and transcription
- structured lesson and job state
- code and permit adapters
- OEM lookup and source retrieval
- audit log

## Spectacles Fit

Snap’s current platform supports:

- internet calls from Spectacles
- WebSocket realtime connections
- AI service calls through Remote Service Gateway
- shared local multiplayer sessions
- Camera Kit for phone and web companion apps

Important constraint:

- Snap Connected Lenses are designed for nearby colocated sessions, not true
  remote telepresence. Remote expert support should therefore use your own
  realtime backend and video path, with Spectacles acting as the onsite AR
  client.

## Safety Model

### Low-risk lessons

- painting
- window measuring
- filter cleaning
- tire pressure
- oil level check

### Expert-gated lessons

- electrical panel interior work
- mini-split refrigerant/electrical service
- brake pad replacement
- permit-signoff decisions

For expert-gated lessons, the product should:

- place a warning banner into the clip prompt
- require remote expert acknowledgement in Assist Mode
- avoid suggesting unsafe DIY completion language
