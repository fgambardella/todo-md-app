#!/usr/bin/env bash
# bump_version.sh — bump the PATCH component of implementer/src/todo_md/VERSION
#
# Usage:
#   bump_version.sh              # bump X.Y.Z -> X.Y.(Z+1) and stage the file
#   bump_version.sh --install-hook
#       # Install .git/hooks/pre-commit that invokes this script; does NOT bump.
#
# Safe to run from any CWD; resolves the repo root via git.
set -euo pipefail

INSTALL_HOOK=0
for arg in "$@"; do
  if [ "$arg" = "--install-hook" ]; then
    INSTALL_HOOK=1
  else
    echo "ERROR: unknown argument: $arg" >&2
    echo "Usage: bump_version.sh [--install-hook]" >&2
    exit 2
  fi
done

ROOT="$(git rev-parse --show-toplevel)"
VERSION_FILE="$ROOT/implementer/src/todo_md/VERSION"

if [ "$INSTALL_HOOK" -eq 1 ]; then
  HOOK_DIR="$ROOT/.git/hooks"
  mkdir -p "$HOOK_DIR"
  HOOK_FILE="$HOOK_DIR/pre-commit"
  {
    printf '%s\n' '#!/bin/sh'
    # Re-resolve the repo root at hook run time so the repo may move.
    printf '%s\n' '"$(git rev-parse --show-toplevel)/implementer/src/scripts/bump_version.sh"'
  } > "$HOOK_FILE"
  chmod +x "$HOOK_FILE"
  echo "pre-commit hook installed at: $HOOK_FILE"
  exit 0
fi

if [ ! -f "$VERSION_FILE" ]; then
  echo "ERROR: VERSION file not found: $VERSION_FILE" >&2
  exit 1
fi

CURRENT="$(cat "$VERSION_FILE")"
# Trim surrounding whitespace.
CURRENT="$(printf '%s' "$CURRENT" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

if ! printf '%s' "$CURRENT" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "ERROR: malformed version '$CURRENT' in $VERSION_FILE (expected X.Y.Z)" >&2
  exit 1
fi

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"
NEW_VERSION="${MAJOR}.${MINOR}.$((10#$PATCH + 1))"

printf '%s\n' "$NEW_VERSION" > "$VERSION_FILE"
git -C "$ROOT" add implementer/src/todo_md/VERSION
echo "Bumped version: $CURRENT -> $NEW_VERSION (staged in git)"