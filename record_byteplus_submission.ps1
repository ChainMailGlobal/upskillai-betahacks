param(
    [string]$RunName = "byteplus_demo",
    [string]$Mode = "assist",
    [string]$ReferencePack = "mini_split_field_service",
    [string]$LessonId = "mini_split_fault_code_triage",
    [string]$InputVideo = "",
    [string]$InputAudio = "",
    [string]$StanPortrait = "",
    [switch]$StopAfterAnimate,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$stage = if ($StopAfterAnimate) { "animate" } else { "digital_twin" }
$cmd = @(
    "python",
    ".\orchestrator.py",
    "--run-name", $RunName,
    "--mode", $Mode,
    "--reference-pack", $ReferencePack,
    "--lesson-id", $LessonId,
    "--stop-after", $stage
)

if ($InputVideo) {
    $cmd += @("--input-video", $InputVideo)
}
if ($InputAudio) {
    $cmd += @("--input-audio", $InputAudio)
}
if ($StanPortrait) {
    $cmd += @("--stan-portrait", $StanPortrait)
}
if ($DryRun) {
    $cmd += "--dry-run"
}

Write-Host ""
Write-Host "== BytePlus submission run ==" -ForegroundColor Cyan
Write-Host ($cmd -join " ")
& $cmd[0] $cmd[1..($cmd.Length - 1)]

Write-Host ""
Write-Host "== BytePlus submission package ==" -ForegroundColor Cyan
python .\prepare_byteplus_submission.py --run-name $RunName

Write-Host ""
Write-Host "Show these next:" -ForegroundColor Green
Write-Host "  runs\\$RunName\\submission\\byteplus_submission_summary.json"
Write-Host "  runs\\$RunName\\submission\\byteplus_talk_track.md"
Write-Host "  runs\\$RunName\\outputs\\clips\\"
Write-Host "  runs\\$RunName\\outputs\\storyboards\\"
