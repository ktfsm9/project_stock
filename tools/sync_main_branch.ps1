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

function Get-DefaultSourceBranch {
    # 1) Prefer current branch when not main
    $current = (& git rev-parse --abbrev-ref HEAD).Trim()
    if ($current -ne 'main') {
        return $current
    }

    # 2) Prefer most recent local codex/* branch
    $localCandidates = (& git for-each-ref --format='%(refname:short)' --sort=-committerdate refs/heads) |
        Where-Object { $_ -ne 'main' }
    $codexLocal = $localCandidates | Where-Object { $_ -like 'codex/*' } | Select-Object -First 1
    if ($codexLocal) {
        return $codexLocal
    }

    # 3) Fallback: most recent non-main local branch
    $firstLocal = $localCandidates | Select-Object -First 1
    if ($firstLocal) {
        return $firstLocal
    }

    return $null
}

# Verify inside git repo
& git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Error: not inside a git repository."
}

if ([string]::IsNullOrWhiteSpace($Source)) {
    $Source = Get-DefaultSourceBranch
    if ([string]::IsNullOrWhiteSpace($Source)) {
        throw "Error: could not auto-detect source branch. Create/switch to a feature branch or pass -Source <branch>."
    }
    Write-Host "Auto-detected source branch: $Source"
}

if ($Source -eq 'main') {
    throw "Source branch is 'main'. Use a feature branch (e.g., codex/...) or omit -Source for auto-detection."
}

# Ensure clean working tree
$porcelain = (& git status --porcelain)
if (-not [string]::IsNullOrWhiteSpace(($porcelain -join "`n"))) {
    throw "Error: working tree is not clean. Commit/stash changes first."
}

# Validate source branch exists locally; if only remote exists, create tracking local branch
& git show-ref --verify --quiet "refs/heads/$Source"
if ($LASTEXITCODE -ne 0) {
    & git show-ref --verify --quiet "refs/remotes/origin/$Source"
    if ($LASTEXITCODE -eq 0) {
        Run-Git -Args @('branch', '--track', $Source, "origin/$Source")
        Write-Host "Created local tracking branch '$Source' from origin/$Source"
    } else {
        $suggest = (& git for-each-ref --format='%(refname:short)' --sort=-committerdate refs/heads refs/remotes/origin | Select-Object -First 10) -join ', '
        throw "Error: source branch '$Source' does not exist. Recent branches: $suggest"
    }
}

# Create/switch main
& git show-ref --verify --quiet "refs/heads/main"
if ($LASTEXITCODE -ne 0) {
    Run-Git -Args @('checkout', '-b', 'main')
} else {
    Run-Git -Args @('checkout', 'main')
}

# FF-only merge
git merge --ff-only $Source
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
