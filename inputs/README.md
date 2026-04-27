Place live pipeline source assets here, or pass explicit file paths on the command line.

The scaffold auto-detects these default filenames:

- `master_recording.mp3`
- `master_recording.wav`
- `master_recording.m4a`
- `master_recording.aac`
- `master_recording.flac`
- `master_recording.mp4`
- `master_recording.mov`
- `stan_portrait.jpg`
- `stan_portrait.jpeg`
- `stan_portrait.png`
- `stan_voice_sample.wav`
- `stan_voice_sample.mp3`

Example:

```powershell
python orchestrator.py --run-name live_smoke --input-video .\inputs\master_recording.mp4
```

If you provide only video, the pipeline extracts audio locally with `ffmpeg` before ASR.
