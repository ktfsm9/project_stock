param(
    [string]$Source,
    [switch]$Push
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$candidates = @(
    (Join-Path $scriptDir "tools/sync_main_branch.ps1"),
    (Join-Path $scriptDir "project_stock/tools/sync_main_branch.ps1")
)

$target = $null
foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
        $target = $candidate
        break
    }
}

if (-not $target) {
    Write-Error "sync script not found. tried:"
    $candidates | ForEach-Object { Write-Error " - $_" }
    Write-Error "hint: run this from your git repo root."
    exit 1
}

& $target -Source $Source -Push:$Push
exit $LASTEXITCODE
