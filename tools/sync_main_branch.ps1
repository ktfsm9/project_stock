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
    $current = (& git rev-parse --abbrev-ref HEAD).Trim()
    if ($current -ne 'main') {
        return $current
    }

    $localCandidates = (& git for-each-ref --format='%(refname:short)' --sort=-committerdate refs/heads) |
        Where-Object { $_ -ne 'main' }

    $codexLocal = $localCandidates | Where-Object { $_ -like 'codex/*' } | Select-Object -First 1
    if ($codexLocal) { return $codexLocal }

    $firstLocal = $localCandidates | Select-Object -First 1
    if ($firstLocal) { return $firstLocal }

    return $null
}

function Get-RecentBranchSuggestions {
    return (& git for-each-ref --format='%(refname:short)' --sort=-committerdate refs/heads refs/remotes/origin |
        Where-Object { $_ -notmatch '^origin/HEAD$' } |
        Select-Object -Unique -First 15)
}

function Resolve-BranchName {
    param([string]$Requested)

    # exact local
    & git show-ref --verify --quiet "refs/heads/$Requested"
    if ($LASTEXITCODE -eq 0) { return $Requested }

    # exact remote
    & git show-ref --verify --quiet "refs/remotes/origin/$Requested"
    if ($LASTEXITCODE -eq 0) { return $Requested }

    # fuzzy candidates: contains requested token
    $all = (& git for-each-ref --format='%(refname:short)' refs/heads refs/remotes/origin |
        ForEach-Object { $_ -replace '^origin/', '' } |
        Where-Object { $_ -ne 'HEAD' } |
        Select-Object -Unique)

    $escaped = [regex]::Escape($Requested)
    $contains = $all | Where-Object { $_ -match $escaped }
    if (($contains | Measure-Object).Count -eq 1) {
        $auto = $contains | Select-Object -First 1
        Write-Host "Requested branch '$Requested' not found; auto-resolved to '$auto'."
        return $auto
    }

    # fallback: if requested looks like codex/*, try matching prefix before random suffix
    if ($Requested -like 'codex/*') {
        $base = $Requested -replace '-[A-Za-z0-9]{4,}$', ''
        if ($base -ne $Requested) {
            $escapedBase = [regex]::Escape($base)
            $baseMatches = $all | Where-Object { $_ -match "^$escapedBase(-[A-Za-z0-9]+)?$" }
            if (($baseMatches | Measure-Object).Count -eq 1) {
                $auto2 = $baseMatches | Select-Object -First 1
                Write-Host "Requested branch '$Requested' not found; auto-resolved to '$auto2'."
                return $auto2
            }
        }
    }

    return $null
}

# Verify inside repo
& git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Error: not inside a git repository."
}

# refresh remote refs for better branch resolution
& git remote get-url origin *> $null
if ($LASTEXITCODE -eq 0) {
    & git fetch origin --prune *> $null
}

if ([string]::IsNullOrWhiteSpace($Source)) {
    $Source = Get-DefaultSourceBranch
    if ([string]::IsNullOrWhiteSpace($Source)) {
        throw "Error: could not auto-detect source branch. Create/switch to a feature branch or pass -Source <branch>."
    }
    Write-Host "Auto-detected source branch: $Source"
}

$resolved = Resolve-BranchName -Requested $Source
if ([string]::IsNullOrWhiteSpace($resolved)) {
    $suggest = (Get-RecentBranchSuggestions) -join ', '
    throw "Error: source branch '$Source' does not exist. Recent branches: $suggest"
}
$Source = $resolved

if ($Source -eq 'main') {
    Write-Host "Source branch resolved to 'main'. Nothing to merge."
    if ($Push) {
        & git remote get-url origin *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "Error: origin remote is not configured."
        }
        Run-Git -Args @('push', 'origin', 'main')
        Write-Host "Verified push: origin/main (already up to date)."
    }
    exit 0
}

# Ensure clean working tree
$porcelain = (& git status --porcelain)
if (-not [string]::IsNullOrWhiteSpace(($porcelain -join "`n"))) {
    throw "Error: working tree is not clean. Commit/stash changes first."
}

# Ensure local source branch exists; if only remote exists then track it
& git show-ref --verify --quiet "refs/heads/$Source"
if ($LASTEXITCODE -ne 0) {
    & git show-ref --verify --quiet "refs/remotes/origin/$Source"
    if ($LASTEXITCODE -eq 0) {
        Run-Git -Args @('branch', '--track', $Source, "origin/$Source")
        Write-Host "Created local tracking branch '$Source' from origin/$Source"
    } else {
        $suggest = (Get-RecentBranchSuggestions) -join ', '
        throw "Error: source branch '$Source' does not exist after resolution. Recent branches: $suggest"
    }
}

# switch main
& git show-ref --verify --quiet "refs/heads/main"
if ($LASTEXITCODE -ne 0) {
    Run-Git -Args @('checkout', '-b', 'main')
} else {
    Run-Git -Args @('checkout', 'main')
}

# ff merge
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
