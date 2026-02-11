param(
    [string]$Source,
    [switch]$Push
)

$ErrorActionPreference = 'Stop'

function Run-Git {
    param([string[]]$Args)
    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

# Verify inside git repo
& git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Error: not inside a git repository."
}

if ([string]::IsNullOrWhiteSpace($Source)) {
    $Source = (& git rev-parse --abbrev-ref HEAD).Trim()
}

if ($Source -eq 'main') {
    throw "Source branch is already 'main'. Nothing to merge."
}

# Ensure clean working tree
$porcelain = (& git status --porcelain)
if (-not [string]::IsNullOrWhiteSpace(($porcelain -join "`n"))) {
    throw "Error: working tree is not clean. Commit/stash changes first."
}

# Validate source branch exists
& git show-ref --verify --quiet "refs/heads/$Source"
if ($LASTEXITCODE -ne 0) {
    throw "Error: source branch '$Source' does not exist."
}

# Create/switch main
& git show-ref --verify --quiet "refs/heads/main"
if ($LASTEXITCODE -ne 0) {
    Run-Git -Args @('checkout', '-b', 'main')
} else {
    Run-Git -Args @('checkout', 'main')
}

# FF-only merge
& git merge --ff-only $Source
if ($LASTEXITCODE -ne 0) {
    throw "Fast-forward merge failed. Resolve diverged history manually (rebase/merge) and retry."
}

Write-Host "Local main updated from '$Source'."

if ($Push) {
    & git remote get-url origin *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Error: origin remote is not configured."
    }
    Run-Git -Args @('push', 'origin', 'main')
    Write-Host "Pushed: origin/main"
}
