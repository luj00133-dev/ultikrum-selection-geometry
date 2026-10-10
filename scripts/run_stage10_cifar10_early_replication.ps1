[CmdletBinding()]
param(
    [string]$ProjectRoot = '',
    [string]$Config = 'configs\stage10_cifar10_early_replication.json',
    [string]$Manifest = 'results\manifests\stage10_cifar10_early_replication.csv',
    [string]$PythonExe = '${USER_HOME}\miniconda3\envs\dl\python.exe',
    [switch]$Run,
    [switch]$Smoke
)
$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest
if($Run -and $Smoke){throw 'Use either -Run or -Smoke.'}
$isDryRun=-not($Run -or $Smoke)
function Full([string]$Path){[IO.Path]::GetFullPath($Path)}
function Assert-InProject([string]$Path,[string]$Root){$candidate=Full $Path;$rootFull=(Full $Root).TrimEnd('\','/');if(-not $candidate.StartsWith($rootFull+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Path outside project: $candidate"}}
function Python-Dict([string]$Json){$literal=$Json.Replace('"',"'");return ($literal -replace '\btrue\b','True' -replace '\bfalse\b','False' -replace '\bnull\b','None')}
function Complete($Row){
    foreach($path in @($Row.output,$Row.system_log,$Row.resolved_config)){if(-not [IO.File]::Exists([string]$path) -or (Get-Item -LiteralPath ([string]$path)).Length -le 0){return $false}}
    $text=Get-Content -LiteralPath ([string]$Row.output) -Raw;if(-not $text.Contains([string]$Row.completion_marker)){return $false}
    $epochs=@([regex]::Matches($text,'(?m)^Epoch\s+(\d+)\s+'));if($epochs.Count -ne [int]$Row.rounds){return $false};for($i=0;$i -lt $epochs.Count;$i++){if([int]$epochs[$i].Groups[1].Value -ne $i){return $false}}
    try{$resolved=Get-Content -LiteralPath ([string]$Row.resolved_config) -Raw|ConvertFrom-Json}catch{return $false}
    $expected=@{epochs=[int]$Row.rounds;seed_partition=[int]$Row.partition_seed;seed_train=[int]$Row.train_seed;system_seed=[int]$Row.system_seed;dataset=[string]$Row.dataset;model=[string]$Row.model;distribution=[string]$Row.distribution;attack=[string]$Row.attack;defense=[string]$Row.vendor_aggregator;system_profile=[string]$Row.system_profile;num_clients=50}
    foreach($key in $expected.Keys){if($resolved.$key -ne $expected[$key]){return $false}}
    try{$systemRows=@(Import-Csv -LiteralPath ([string]$Row.system_log))}catch{return $false};if($systemRows.Count -ne [int]$Row.expected_system_rows){return $false}
    $rounds=$systemRows|Group-Object round;if($rounds.Count -ne [int]$Row.rounds){return $false};foreach($group in $rounds){if($group.Count -ne 50 -or @($group.Group.client_id|Sort-Object -Unique).Count -ne 50){return $false}}
    return $true
}
$root=if([string]::IsNullOrWhiteSpace($ProjectRoot)){Full (Join-Path $PSScriptRoot '..')}else{Full $ProjectRoot}
$required=Full '${PROJECT_ROOT}';if(-not $isDryRun -and -not $root.Equals($required,[StringComparison]::OrdinalIgnoreCase)){throw 'Real runs are restricted to ${PROJECT_ROOT}'}
if(-not(Test-Path -LiteralPath $PythonExe -PathType Leaf)){throw "Python not found: $PythonExe"}
$configFull=if([IO.Path]::IsPathRooted($Config)){Full $Config}else{Full (Join-Path $root $Config)};$manifestFull=if([IO.Path]::IsPathRooted($Manifest)){Full $Manifest}else{Full (Join-Path $root $Manifest)}
$builder=Join-Path $root 'src\build_stage10_manifest.py';$builderArgs=@('--config',$configFull,'--project-root',$root)
if($Smoke){$json=(& $PythonExe $builder @builderArgs --smoke --json|Out-String);if($LASTEXITCODE -ne 0){throw 'Stage 10 smoke builder failed'};$parsed=$json|ConvertFrom-Json;$rows=@();foreach($item in $parsed){$rows+=$item}}
elseif($isDryRun){$json=(& $PythonExe $builder @builderArgs --dry-run --json|Out-String);if($LASTEXITCODE -ne 0){throw 'Stage 10 dry-run builder failed'};$parsed=$json|ConvertFrom-Json;$rows=@();foreach($item in $parsed){$rows+=$item}}
else{Assert-InProject $manifestFull $root;& $PythonExe $builder @builderArgs --out $manifestFull;if($LASTEXITCODE -ne 0){throw 'Stage 10 manifest builder failed'};$rows=@(Import-Csv -LiteralPath $manifestFull)}
$expectedCount=if($Smoke){3}else{27};if($rows.Count -ne $expectedCount){throw "Expected $expectedCount Stage 10 cells, got $($rows.Count)"}
$resultRoot=Full (Join-Path $root $(if($Smoke){'results\smoke\stage10_cifar10_early_replication'}else{'results\raw\stage10_cifar10_early_replication'}));$vendorRoot=Join-Path $root 'vendor\FLPoison';$planned=0;$skipped=0
foreach($row in $rows){
    foreach($path in @($row.output,$row.system_log,$row.resolved_config,$row.base_config)){Assert-InProject ([string]$path) $root};if(-not(Full ([string]$row.output)).StartsWith($resultRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Stage 10 output root violation'}
    if(Complete $row){$skipped++;Write-Host "[SKIP complete] $($row.run_id)";continue};$planned++
    $command=@('main.py','--config',[string]$row.base_config,'--epochs',[string]$row.rounds,'--seed',[string]$row.train_seed,'--seed_partition',[string]$row.partition_seed,'--seed_train',[string]$row.train_seed,'--algorithm',[string]$row.algorithm,'--dataset',[string]$row.dataset,'--model',[string]$row.model,'--distribution',[string]$row.distribution,'--dirichlet_alpha',[string]$row.dirichlet_alpha,'--attack',[string]$row.attack,'--defense',[string]$row.vendor_aggregator,'--defense_params',(Python-Dict ([string]$row.defense_params)),'--system_profile',[string]$row.system_profile,'--system_seed',[string]$row.system_seed,'--output',[string]$row.output,'--system_log',[string]$row.system_log)
    if($isDryRun){Write-Host '[DRYRUN]' $PythonExe ($command -join ' ');continue};Write-Host "[RUN] $($row.run_id)";Push-Location $vendorRoot;try{& $PythonExe @command;if($LASTEXITCODE -ne 0){throw "Cell failed: $($row.run_id)"}}finally{Pop-Location};if(-not(Complete $row)){throw "Incomplete Stage 10 result: $($row.run_id)"}
}
if($isDryRun){Write-Host "DryRun complete: 27 cells, $planned runnable, $skipped complete; no manifest or training output written."}elseif($Smoke){Write-Host "Stage 10 smoke complete: 3 cells, $planned run, $skipped skipped; excluded from formal analysis."}else{Write-Host "Stage 10 formal complete: 27 cells, $planned run, $skipped skipped."}
