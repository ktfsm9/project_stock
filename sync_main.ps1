param(
    [string]$Source,
    [switch]$Push
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $scriptDir "tools/sync_main_branch.ps1"

if (-not (Test-Path $target)) {
    throw "sync script not found: $target"
}

& $target -Source $Source -Push:$Push
exit $LASTEXITCODE
