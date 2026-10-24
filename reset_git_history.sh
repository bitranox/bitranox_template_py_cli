#!/usr/bin/env bash

set -euo pipefail

echo "Preparing to squash repository history..."

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: run this script inside a Git repository." >&2
    exit 1
fi

current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || true)"
if [[ -z "$current_branch" ]]; then
    echo "Error: could not determine current branch. Check out a branch and retry." >&2
    exit 1
fi

message_file="$(mktemp)"
trap 'rm -f "$message_file"' EXIT

# IntelliJ settings are machine-local and never published, ignored or not: drop them from the
# index, keep them on disk, and leave them out of every staging and cleanliness check below.
not_idea=':(exclude).idea'
git rm -r --cached .idea >/dev/null 2>&1 || true

# Stage EVERYTHING that is not ignored, untracked files included: after rename.sh the renamed
# package is untracked, and a tracked-only snapshot would force-push a tree without it.
git add -A -- . "$not_idea"
if ! git diff --cached --quiet; then
    echo "Committing the working tree before the reset; these changes will be published:"
    git diff --cached --name-status
    printf '%s\n' "chore: checkpoint before history reset" >"$message_file"
    git commit -q -F "$message_file"
fi

# Nothing may be left behind, untracked files included: whatever is not in HEAD is not pushed.
if [[ -n "$(git status --porcelain -- . "$not_idea")" ]]; then
    echo "Error: working tree is not clean after the checkpoint commit. Aborting." >&2
    git status --short -- . "$not_idea" >&2
    exit 1
fi

tree_sha="$(git rev-parse 'HEAD^{tree}')"
printf '%s\n' "chore: reset history" >"$message_file"
new_commit="$(git commit-tree "$tree_sha" -F "$message_file")"
git reset --hard "$new_commit"

remote="${1:-}"
if [[ -z "$remote" ]]; then
    remote="$(git remote | head -n1 || true)"
fi

if [[ -n "$remote" ]]; then
    echo "Force pushing rewritten history to remote '$remote'..."
    git push --force "$remote" "$current_branch"
else
    echo "No remote configured. Local history rewritten only."
fi

echo "History reset complete. Ignored files were left untouched and not published."
