#!/usr/bin/env bash
set -euo pipefail

# Sync current branch changes into local main, then optionally push origin/main.
#
# Usage:
#   bash tools/sync_main_branch.sh [--push] [--source <branch>]
#
# Examples:
#   bash tools/sync_main_branch.sh --source work
#   bash tools/sync_main_branch.sh --source work --push

PUSH=0
SOURCE_BRANCH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push)
      PUSH=1
      shift
      ;;
    --source)
      SOURCE_BRANCH="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: bash tools/sync_main_branch.sh [--push] [--source <branch>]" >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

if [[ -z "$SOURCE_BRANCH" ]]; then
  SOURCE_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
fi

if [[ "$SOURCE_BRANCH" == "main" ]]; then
  echo "Source branch is already 'main'. Nothing to merge." >&2
  exit 1
fi

# Ensure working tree is clean before branch switching
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is not clean. Commit/stash changes first." >&2
  exit 1
fi

if ! git show-ref --verify --quiet "refs/heads/$SOURCE_BRANCH"; then
  echo "Error: source branch '$SOURCE_BRANCH' does not exist." >&2
  exit 1
fi

# Create main if missing
if ! git show-ref --verify --quiet refs/heads/main; then
  git checkout -b main
else
  git checkout main
fi

# Merge source branch into main (fast-forward when possible)
git merge --ff-only "$SOURCE_BRANCH" || {
  echo "Fast-forward merge failed. Resolve diverged history manually (rebase/merge) and retry." >&2
  exit 1
}

echo "Local main updated from '$SOURCE_BRANCH'."

if [[ "$PUSH" -eq 1 ]]; then
  if git remote get-url origin >/dev/null 2>&1; then
    git push origin main
    echo "Pushed: origin/main"
  else
    echo "Warning: origin remote is not configured. Skipped push." >&2
    exit 2
  fi
fi
