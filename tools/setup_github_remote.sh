#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash tools/setup_github_remote.sh <github_repo_url> [branch]
# Example:
#   bash tools/setup_github_remote.sh https://github.com/ktfsm9/project_stock.git main

REPO_URL="${1:-}"
TARGET_BRANCH="${2:-main}"

if [[ -z "$REPO_URL" ]]; then
  echo "Usage: bash tools/setup_github_remote.sh <github_repo_url> [branch]" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: current directory is not a git repository." >&2
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  CURRENT_URL="$(git remote get-url origin)"
  if [[ "$CURRENT_URL" != "$REPO_URL" ]]; then
    git remote set-url origin "$REPO_URL"
    echo "Updated origin URL: $CURRENT_URL -> $REPO_URL"
  else
    echo "Origin already configured: $REPO_URL"
  fi
else
  git remote add origin "$REPO_URL"
  echo "Added origin: $REPO_URL"
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [[ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]]; then
  if git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH"; then
    git checkout "$TARGET_BRANCH"
    echo "Switched to existing branch: $TARGET_BRANCH"
  else
    git checkout -b "$TARGET_BRANCH"
    echo "Created and switched to branch: $TARGET_BRANCH"
  fi
fi

# Set upstream on first push; if branch already exists remotely this is idempotent.
git push -u origin "$TARGET_BRANCH"

echo "Done. Local repository is now linked to $REPO_URL and tracking origin/$TARGET_BRANCH"
