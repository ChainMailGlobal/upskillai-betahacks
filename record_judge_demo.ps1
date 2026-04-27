$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "== UpSkillAI judge demo: reference packs ==" -ForegroundColor Cyan
python .\reference_packs.py

Write-Host ""
Write-Host "== UpSkillAI judge demo: mini-split pack ==" -ForegroundColor Cyan
python .\reference_packs.py --pack mini_split_field_service

Write-Host ""
Write-Host "== UpSkillAI judge demo: dry-run lesson decomposition ==" -ForegroundColor Cyan
python .\orchestrator.py --run-name judge_demo --dry-run --mode learn --reference-pack mini_split_field_service --lesson-id mini_split_fault_code_triage --stop-after decompose

Write-Host ""
Write-Host "== UpSkillAI judge demo: build kdemo package ==" -ForegroundColor Cyan
if ($env:MISTRAL_API_KEY) {
    python .\build_kdemo.py --run-name judge_demo --voice auto
} else {
    Write-Host "MISTRAL_API_KEY not set. Building silent animatic fallback." -ForegroundColor Yellow
    python .\build_kdemo.py --run-name judge_demo --voice none
}

Write-Host ""
Write-Host "Outputs:" -ForegroundColor Green
Write-Host "  runs\\judge_demo\\run_context.json"
Write-Host "  runs\\judge_demo\\stages\\decompose.json"
Write-Host "  runs\\judge_demo\\kdemo\\kdemo_plan.json"
Write-Host "  runs\\judge_demo\\kdemo\\kdemo_animatic.mp4"
