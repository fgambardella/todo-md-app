#!/usr/bin/env bash
# release_package.sh — produce the release artifact for todo-md.
#
# Usage:
#   scripts/release_package.sh
#       # Builds dist/todo-md.app (via build_app.sh) and packages it into
#       # dist/todo-md-<version>-arm64.zip for upload to a GitHub release.
#
# Safe to run from the repo root or from implementer/src (or anywhere else);
# all paths are resolved relative to this script's location.
#
# What it does:
#   1. Runs scripts/build_app.sh to (re)build dist/todo-md.app.
#   2. Reads todo_md/VERSION and validates it is a strict X.Y.Z semantic
#      version; aborts with a clear error on a malformed value.
#   3. Removes any pre-existing dist/todo-md-<version>-arm64.zip.
#   4. Zips the bundle with macOS `ditto -c -k --noextattr --noqtn` so that
#      todo-md.app sits at the ZIP root (no __MACOSX junk entries), producing
#      dist/todo-md-<version>-arm64.zip.
#   5. Prints the zip path, its size in bytes, its SHA-256 digest, and a
#      pointer to the "Packaging and release" section of the README for the
#      GitHub upload step.
#
# The release artifacts (build/, dist/) are intentionally NOT committed to git.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$SRC_DIR/dist"
APP_BUNDLE="$DIST_DIR/todo-md.app"
VERSION_FILE="$SRC_DIR/todo_md/VERSION"

# --- 1. Build the app bundle ------------------------------------------------------
bash "$SCRIPT_DIR/build_app.sh"

# --- 2. Read and validate the version ----------------------------------------------
if [ ! -f "$VERSION_FILE" ]; then
  echo "ERROR: version file not found: $VERSION_FILE" >&2
  exit 1
fi
VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: malformed version in $VERSION_FILE: '$VERSION' (expected X.Y.Z)." >&2
  exit 1
fi

# --- 3. Remove any pre-existing release zip ------------------------------------------
ZIP_PATH="$DIST_DIR/todo-md-${VERSION}-arm64.zip"
rm -f "$ZIP_PATH"

# --- 4. Zip the bundle with todo-md.app at the archive root ---------------------------
if [ ! -d "$APP_BUNDLE" ]; then
  echo "ERROR: app bundle not found after build: $APP_BUNDLE" >&2
  exit 1
fi
if ! command -v ditto >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1; then
  echo "ERROR: 'ditto' (macOS built-in) is required to create the release zip." >&2
  exit 1
fi

# `ditto -c -k <dir> <zip>` archives the *contents* of <dir>, so stage the
# bundle one level down to keep todo-md.app as the top-level entry.
STAGE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/todo-md-release.XXXXXX")"
trap 'rm -rf "$STAGE_DIR"' EXIT
ditto "$APP_BUNDLE" "$STAGE_DIR/todo-md.app"
ditto -c -k --noextattr --noqtn "$STAGE_DIR" "$ZIP_PATH"
if [ ! -f "$ZIP_PATH" ]; then
  echo "ERROR: release zip was not created: $ZIP_PATH" >&2
  exit 1
fi

# --- 5. Report --------------------------------------------------------------------------
ZIP_SIZE="$(wc -c < "$ZIP_PATH" | tr -d '[:space:]')"
ZIP_SHA256="$(shasum -a 256 "$ZIP_PATH" | awk '{print $1}')"
echo "Release zip: $ZIP_PATH"
echo "Size: ${ZIP_SIZE} bytes"
echo "SHA-256: $ZIP_SHA256"
echo "Next: upload this zip as a GitHub release asset — see the 'Packaging and release' section of the README."