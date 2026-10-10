[CmdletBinding()]
param(
    [string]$ProjectRoot = '',
    [string]$Config = 'configs\stage8_a05_converged.json',
    [string]$Manifest = 'results\manifests\stage8_a05_converged_5seed.csv',
    [string]$PythonExe = '${USER_HOME}\miniconda3\envs\dl\python.exe',
    [switch]$Run,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($Run -and $DryRun) { throw 'Use either -Run or -DryRun.' }
$isDryRun = -not $Run

function Full([string]$Path) { [System.IO.Path]::GetFullPath($Path) }
function Assert-InProject([string]$Path, [string]$Root) {
    $candidate = Full $Path
    $rootFull = (Full $Root).TrimEnd('\','/')
    if (-not $candidate.StartsWith($rootFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path outside project: $candidate"
    }
}
function Python-Dict([string]$Json) {
    $literal = $Json.Replace('"', "'")
    $literal = $literal -replace '\btrue\b','True' -replace '\bfalse\b','False' -replace '\bnull\b','None'
    return $literal
}
function Complete($Row) {
    foreach ($path in @($Row.output,$Row.system_log,$Row.resolved_config)) {
        if (-not [IO.File]::Exists([string]$path) -or (Get-Item -LiteralPath ([string]$path)).Length -le 0) { return $false }
    }
    if (-not (Get-Content -LiteralPath ([string]$Row.output) -Raw).Contains([string]$Row.completion_marker)) { return $false }
    try { $resolved = Get-Content -LiteralPath ([string]$Row.resolved_config) -Raw | ConvertFrom-Json } catch { return $false }
    foreach ($name in @('defense_params','system_profile','system_seed','seed_partition','seed_train')) {
        if (-not ($resolved.PSObject.Properties.Name -contains $name)) { return $false }
    }
    try { $systemRows = @(Import-Csv -LiteralPath ([string]$Row.system_log)) } catch { return $false }
    if ($systemRows.Count -ne [int]$Row.expected_system_rows) { return $false }
    foreach ($name in @('round','client_id','resource_group','effective_staleness','aggregator_score','selected')) {
        if (-not ($systemRows[0].PSObject.Properties.Name -contains $name)) { return $false }
    }
    return $true
}

$root = if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { Full (Join-Path $PSScriptRoot '..') } else { Full $ProjectRoot }
$required = Full '${PROJECT_ROOT}'
if (-not $isDryRun -and -not $root.Equals($required,[StringComparison]::OrdinalIgnoreCase)) { throw 'Real runs are restricted to ${PROJECT_ROOT}' }
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw "Python not found: $PythonExe" }
$configFull = if ([IO.Path]::IsPathRooted($Config)) { Full $Config } else { Full (Join-Path $root $Config) }
$manifestFull = if ([IO.Path]::IsPathRooted($Manifest)) { Full $Manifest } else { Full (Join-Path $root $Manifest) }
$builder = Join-Path $root 'src\build_stage8_manifest.py'
$builderArgs = @('--config',$configFull,'--project-root',$root)
if ($isDryRun) {
    $json = (& $PythonExe $builder @builderArgs --dry-run --json | Out-String)
    if ($LASTEXITCODE -ne 0) { throw 'Stage 8 dry-run builder failed' }
    $parsed = $json | ConvertFrom-Json
    $rows = @()
    if ($parsed -is [System.Array]) { foreach ($item in $parsed) { $rows += $item } }
    else { $rows += $parsed }
} else {
    Assert-InProject $manifestFull $root
    & $PythonExe $builder @builderArgs --out $manifestFull
    if ($LASTEXITCODE -ne 0) { throw 'Stage 8 manifest builder failed' }
    $rows = @(Import-Csv -LiteralPath $manifestFull)
}
if ($rows.Count -ne 15) { throw "Expected 15 Stage 8 cells, got $($rows.Count)" }
$resultRoot = Full (Join-Path $root 'results\raw\stage8_a05_converged_5seed')
$vendorRoot = Join-Path $root 'vendor\FLPoison'
$planned=0; $skipped=0
foreach ($row in $rows) {
    foreach ($path in @($row.output,$row.system_log,$row.resolved_config,$row.base_config)) { Assert-InProject ([string]$path) $root }
    if (-not (Full ([string]$row.output)).StartsWith($resultRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Stage 8 output root violation' }
    if (Complete $row) { $skipped++; Write-Host "[SKIP complete] $($row.run_id)"; continue }
    $planned++
    $command = @('main.py','--config',[string]$row.base_config,'--epochs',[string]$row.rounds,
        '--seed',[string]$row.train_seed,'--seed_partition',[string]$row.partition_seed,
        '--seed_train',[string]$row.train_seed,'--algorithm',[string]$row.algorithm,
        '--dataset',[string]$row.dataset,'--model',[string]$row.model,
        '--distribution',[string]$row.distribution,'--dirichlet_alpha',[string]$row.dirichlet_alpha,
        '--attack',[string]$row.attack,'--defense',[string]$row.vendor_aggregator,
        '--defense_params',(Python-Dict ([string]$row.defense_params)),
        '--system_profile',[string]$row.system_profile,'--system_seed',[string]$row.system_seed,
        '--output',[string]$row.output,'--system_log',[string]$row.system_log)
    if ($isDryRun) { Write-Host '[DRYRUN]' $PythonExe ($command -join ' '); continue }
    Write-Host "[RUN] $($row.run_id)"
    Push-Location $vendorRoot
    try { & $PythonExe @command; if ($LASTEXITCODE -ne 0) { throw "Cell failed: $($row.run_id)" } } finally { Pop-Location }
    if (-not (Complete $row)) { throw "Incomplete Stage 8 result: $($row.run_id)" }
}
if ($isDryRun) { Write-Host "DryRun complete: 15 cells, $planned runnable, $skipped complete; no manifest or training output written." }
else { Write-Host "Stage 8 complete: 15 cells, $planned run, $skipped skipped." }
