$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$blender = Get-ChildItem 'C:\Program Files\Blender Foundation' -Filter blender.exe -Recurse -ErrorAction Stop |
    Sort-Object FullName -Descending |
    Select-Object -First 1 -ExpandProperty FullName

if (-not $blender) {
    throw 'Blender executable was not found under C:\Program Files\Blender Foundation.'
}

$primary = Join-Path $repo 'chair.blend'
$backup = Join-Path $repo 'chair.blend1'
$inspect = Join-Path $PSScriptRoot 'inspect_blend.py'
$compare = Join-Path $PSScriptRoot 'compare_blend_reports.py'
$outDir = Join-Path $repo 'audit'

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Host "Blender: $blender"
Write-Host "Repo:    $repo"

$targets = @()
if (Test-Path $primary) { $targets += @{ Path = $primary; Name = 'chair' } }
if (Test-Path $backup) { $targets += @{ Path = $backup; Name = 'chair_backup' } }

if ($targets.Count -eq 0) {
    throw "Neither chair.blend nor chair.blend1 exists in $repo"
}

foreach ($target in $targets) {
    $json = Join-Path $outDir ($target.Name + '.json')
    Write-Host "`n=== Auditing $($target.Path) ==="
    & $blender --background $target.Path --python $inspect -- --out $json
    if ($LASTEXITCODE -ne 0) {
        throw "Blender audit failed for $($target.Path) with exit code $LASTEXITCODE"
    }
}

$primaryJson = Join-Path $outDir 'chair.json'
$backupJson = Join-Path $outDir 'chair_backup.json'
if ((Test-Path $primaryJson) -and (Test-Path $backupJson)) {
    $diff = Join-Path $outDir 'comparison.json'
    Write-Host "`n=== Comparing chair.blend and chair.blend1 ==="
    python $compare $primaryJson $backupJson --out $diff
    if ($LASTEXITCODE -ne 0) {
        throw "Report comparison failed with exit code $LASTEXITCODE"
    }
}

Write-Host "`n=== Audit outputs ==="
Get-ChildItem $outDir -File | Select-Object Name, Length, LastWriteTime
Write-Host "`nAudit complete. Send me the files from $outDir or paste comparison.json for interpretation."
