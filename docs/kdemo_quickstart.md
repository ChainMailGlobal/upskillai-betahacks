# KDemo Quickstart

Use this when you need a coherent demo asset quickly.

## Fastest Path

```powershell
cd c:\OpenClawLens\Assets\upskillai_betahacks
python build_kdemo.py --run-name kdemo_fast
```

If you want real narration through Mistral Voxtral TTS instead of the local Windows fallback:

```powershell
$env:MISTRAL_API_KEY="your-real-key"
python build_kdemo.py --run-name kdemo_fast --voice mistral
```

For a consistent cloned voice, either set a saved `voice_id`:

```powershell
$env:MISTRAL_API_KEY="your-real-key"
$env:MISTRAL_VOICE_ID="your-saved-voice-id"
python build_kdemo.py --run-name kdemo_fast --voice mistral
```

Or clone from a short sample clip instead of a saved voice:

```powershell
$env:MISTRAL_API_KEY="your-real-key"
python build_kdemo.py --run-name kdemo_fast --voice mistral --mistral-ref-audio .\inputs\stan_voice_sample.wav
```

Outputs:

- `runs/kdemo_fast/kdemo/kdemo_animatic.mp4`
- `runs/kdemo_fast/kdemo/narration_script.txt`
- `runs/kdemo_fast/kdemo/kdemo_plan.json`
- `runs/kdemo_fast/kdemo/captions.srt`

The default hero example is mini-split fault triage because it shows:

- Learn Mode structure
- Assist Mode expert escalation
- backend lookups for model, fault codes, and manuals

## Swap the Hero Lesson

```powershell
python build_kdemo.py `
  --run-name kdemo_window `
  --hero-pack window_replacement_basics `
  --hero-lesson window_measure_opening
```

## What This Demo Is

- a narrated text animatic
- driven by the trade reference library
- usable immediately for pitch/demo flow

If `MISTRAL_API_KEY` is present and either `MISTRAL_VOICE_ID` or `inputs/stan_voice_sample.*`
exists, `--voice auto` will use that voice clone. If only `MISTRAL_API_KEY` is present,
`--voice auto` will still use Mistral with its default voice behavior.

## What To Replace Next

Replace slides 3 and 4 first with:

- Seedream keyframes
- Seedance-generated AR overlay clips
- real remote-assist UI captures from Spectacles or phone
