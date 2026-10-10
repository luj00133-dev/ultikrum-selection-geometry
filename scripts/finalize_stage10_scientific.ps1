param(
    [string]$Python = "${USER_HOME}\miniconda3\envs\dl\python.exe",
    [switch]$Run
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python runtime not found: $Python"
}

$AuditPath = Join-Path $ProjectRoot "results\processed\stage10_cifar10_early_replication\terminal_progress_audit.json"
$AuditText = & $Python "src\audit_stage10_progress.py"
if ($LASTEXITCODE -ne 0) {
    throw "Stage 10 progress auditor failed with exit code $LASTEXITCODE"
}
$Audit = $AuditText | ConvertFrom-Json

$Counts = $Audit.counts
$Ready = (
    $Audit.status -eq "complete" -and
    [int]$Counts.complete -eq 27 -and
    [int]$Counts.partial -eq 0 -and
    [int]$Counts.missing -eq 0 -and
    [int]$Counts.invalid -eq 0
)

if (-not $Ready) {
    $Message = (
        "Stage 10 is not terminal: status={0}, complete={1}, partial={2}, missing={3}, invalid={4}. " +
        "No analyzer or manuscript renderer was run."
    ) -f $Audit.status, $Counts.complete, $Counts.partial, $Counts.missing, $Counts.invalid
    [Console]::Error.WriteLine($Message)
    exit 3
}

if (-not $Run) {
    Write-Output "Stage 10 is 27/27 complete and integrity-valid. Re-run with -Run to execute the frozen closure chain."
    exit 0
}

$CodeFreezeText = & $Python "src\verify_stage10_scientific_code_freeze.py"
if ($LASTEXITCODE -ne 0) {
    throw "Stage 10 scientific-code freeze verification failed with exit code $LASTEXITCODE."
}
$CodeFreeze = $CodeFreezeText | ConvertFrom-Json
if ($CodeFreeze.status -ne "passed" -or $CodeFreeze.manifest_sha256 -ne $Audit.manifest_sha256) {
    throw "Stage 10 scientific-code freeze does not match the audited manifest."
}

$AuditDirectory = Split-Path -Parent $AuditPath
New-Item -ItemType Directory -Path $AuditDirectory -Force | Out-Null
$AuditText | Set-Content -LiteralPath $AuditPath -Encoding utf8

$Steps = @(
    "src\analyze_stage10_cifar10.py",
    "src\verify_stage10_independent.py",
    "src\verify_stage10_semantics_independent.py",
    "src\render_stage10_results_report.py",
    "src\verify_stage10_results_report_independent.py",
    "src\render_stage10_manuscript_insert.py",
    "src\assemble_stage10_manuscript_candidate.py"
)

foreach ($Step in $Steps) {
    Write-Output "Running $Step"
    & $Python $Step
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE; closure stopped."
    }
}

$Processed = Join-Path $ProjectRoot "results\processed\stage10_cifar10_early_replication"
$CandidateVerificationPath = Join-Path $Processed "manuscript_candidate_verification.json"
$CandidateVerificationText = & $Python "src\verify_manuscript_stage9_claims.py" `
    --manuscript "manuscript/manuscript_stage10_candidate.md" `
    --supplement "manuscript/supplementary_stage10_candidate.md"
if ($LASTEXITCODE -ne 0) {
    throw "Independent manuscript-candidate verification failed with exit code $LASTEXITCODE."
}
$CandidateVerification = $CandidateVerificationText | ConvertFrom-Json
if ($CandidateVerification.status -ne "passed" -or $CandidateVerification.stage10_state -eq "pending") {
    throw "Candidate verifier did not establish a terminal passed manuscript state."
}
$CandidateVerificationText | Set-Content -LiteralPath $CandidateVerificationPath -Encoding utf8

$Required = @(
    "analysis.json",
    "scientific_code_verification.json",
    "independent_verification.json",
    "semantic_verification.json",
    "results_report_audit.json",
    "results_report_verification.json",
    "manuscript_insert_audit.json",
    "manuscript_candidate_audit.json",
    "manuscript_candidate_verification.json",
    "raw_sha256.csv"
)
$Ledger = [ordered]@{}
foreach ($Name in $Required) {
    $Path = Join-Path $Processed $Name
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Closure output missing: $Path"
    }
    $Ledger[$Name] = [ordered]@{
        path = $Path
        bytes = (Get-Item -LiteralPath $Path).Length
        sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$Analysis = Get-Content -LiteralPath (Join-Path $Processed "analysis.json") -Raw | ConvertFrom-Json
$Independent = Get-Content -LiteralPath (Join-Path $Processed "independent_verification.json") -Raw | ConvertFrom-Json
$Semantic = Get-Content -LiteralPath (Join-Path $Processed "semantic_verification.json") -Raw | ConvertFrom-Json
$InsertAudit = Get-Content -LiteralPath (Join-Path $Processed "manuscript_insert_audit.json") -Raw | ConvertFrom-Json

if ($Independent.status -ne "passed" -or $Semantic.status -ne "passed" -or $InsertAudit.status -ne "rendered") {
    throw "A required independent or rendering gate did not pass."
}

$Closure = [ordered]@{
    status = "scientific_closure_generated"
    generated_at_utc = [DateTime]::UtcNow.ToString("o")
    manifest_sha256 = $Audit.manifest_sha256
    complete_cells = [int]$Counts.complete
    failed_learning_cells = @($Audit.failed_learning_cells)
    analysis_status = $Analysis.status
    transfer_gate_pass = [bool]$Analysis.transfer_gate_pass
    numeric_verification_status = $Independent.status
    semantic_verification_status = $Semantic.status
    manuscript_terminal_state = $InsertAudit.terminal_state
    files = $Ledger
    next_action = "Review and independently verify the generated manuscript candidate; do not infer author declarations."
}
$ClosurePath = Join-Path $Processed "scientific_closure.json"
$Closure | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ClosurePath -Encoding utf8
Write-Output "Scientific closure generated: $ClosurePath"

Write-Output "Building de-identified scientific reproducibility bundle"
$BundleText = & $Python "src\build_scientific_reproducibility_bundle.py"
if ($LASTEXITCODE -ne 0) {
    throw "Scientific reproducibility bundle build failed with exit code $LASTEXITCODE."
}
$Bundle = $BundleText | ConvertFrom-Json
if ($Bundle.status -ne "built" -or $Bundle.raw_logs_included -ne $false) {
    throw "Scientific reproducibility bundle did not pass its terminal isolation gate."
}
if ($Bundle.scientific_closure_sha256 -ne (Get-FileHash -LiteralPath $ClosurePath -Algorithm SHA256).Hash.ToLowerInvariant()) {
    throw "Scientific reproducibility bundle references a different closure hash."
}
Write-Output "Scientific reproducibility bundle generated: $($Bundle.zip)"

$BundleVerificationText = & $Python "src\verify_reproducibility_bundle_independent.py"
if ($LASTEXITCODE -ne 0) {
    throw "Independent reproducibility-bundle verification failed with exit code $LASTEXITCODE."
}
$BundleVerification = $BundleVerificationText | ConvertFrom-Json
if ($BundleVerification.status -ne "passed" -or $BundleVerification.raw_and_smoke_excluded -ne $true) {
    throw "Independent reproducibility-bundle verification did not pass its isolation gate."
}
if ($BundleVerification.zip_sha256 -ne $Bundle.zip_sha256) {
    throw "Independent reproducibility-bundle verifier returned a different ZIP hash."
}
Write-Output "Independent reproducibility-bundle verification passed."
