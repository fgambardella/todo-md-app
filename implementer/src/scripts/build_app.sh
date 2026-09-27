#!/usr/bin/env bash
# build_app.sh — build a self-contained macOS (Apple Silicon/arm64) app bundle
# for the todo-md application using PyInstaller.
#
# Usage:
#   scripts/build_app.sh
#       # Build dist/todo-md.app from the `python -m todo_md` entry point.
#
# Safe to run from the repo root or from implementer/src (or anywhere else);
# all paths are resolved relative to this script's location.
#
# What it does:
#   1. Host guard: aborts unless the host architecture is arm64 (Apple Silicon).
#   2. Ensures PyInstaller is installed in the project venv (implementer/src/.venv);
#      PyInstaller is a dev-only build dependency (see requirements-dev.txt),
#      the todo_md package itself keeps stdlib-only imports.
#   3. Runs PyInstaller with --onedir --windowed --name todo-md, placing
#      workpath/specpath under implementer/src/build/ and the bundle at
#      implementer/src/dist/todo-md.app. Package data (assets, VERSION) is
#      collected via --collect-data so the frozen app finds them.
#   4. Smoke check: launches dist/todo-md.app/Contents/MacOS/todo-md, waits
#      ~3s, asserts the process is still alive and its stderr contains no
#      traceback, then terminates it. Exits non-zero on any failure.
#
# The build artifacts (build/, dist/) are intentionally NOT committed to git.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PY="$SRC_DIR/.venv/bin/python"
BUILD_DIR="$SRC_DIR/build"
DIST_DIR="$SRC_DIR/dist"

# --- Host guard: this build targets Apple Silicon --------------------------------
ARCH="$(uname -m)"
if [ "$ARCH" != "arm64" ]; then
  echo "ERROR: build_app.sh targets Apple Silicon (arm64) macOS hosts only;" \
       "detected architecture is '$ARCH'." >&2
  exit 1
fi

# --- Venv guard -------------------------------------------------------------------
if [ ! -x "$VENV_PY" ]; then
  echo "ERROR: project venv interpreter not found: $VENV_PY" >&2
  exit 1
fi

# --- PyInstaller (dev-only dependency) ---------------------------------------------
if ! "$VENV_PY" -c "import PyInstaller" >/dev/null 2>&1; then
  echo "PyInstaller not found in venv; installing (dev-only build dependency)..."
  "$VENV_PY" -m pip install pyinstaller
fi

# --- Build the bundle ----------------------------------------------------------------
echo "Building todo-md.app with PyInstaller (--onedir --windowed)..."
# Run from SRC_DIR so the todo_md package is importable for module analysis.
(
  cd "$SRC_DIR"
  "$VENV_PY" -m PyInstaller \
    --noconfirm --clean \
    --onedir --windowed --name todo-md \
    --workpath "$BUILD_DIR/work" \
    --specpath "$BUILD_DIR" \
    --distpath "$DIST_DIR" \
    --collect-data todo_md \
    todo_md/__main__.py
)

APP_BIN="$DIST_DIR/todo-md.app/Contents/MacOS/todo-md"
if [ ! -x "$APP_BIN" ]; then
  echo "ERROR: expected bundle executable not found: $APP_BIN" >&2
  exit 1
fi

# --- Smoke check: launch the bundle, verify it stays up without a traceback ---------
echo "Smoke check: launching $APP_BIN ..."
STDERR_FILE="$(mktemp "${TMPDIR:-/tmp}/todo-md-build.XXXXXX")"
trap 'rm -f "$STDERR_FILE"' EXIT

"$APP_BIN" >/dev/null 2>"$STDERR_FILE" &
APP_PID=$!

sleep 3

FAILED=0
if ! kill -0 "$APP_PID" 2>/dev/null; then
  echo "ERROR: bundle process (pid $APP_PID) exited within 3s of launch." >&2
  FAILED=1
fi
if grep -q "Traceback" "$STDERR_FILE"; then
  echo "ERROR: traceback detected in bundle stderr:" >&2
  FAILED=1
fi
if [ "$FAILED" -ne 0 ]; then
  echo "----- captured bundle stderr -----" >&2
  cat "$STDERR_FILE" >&2
  echo "----------------------------------" >&2
fi

# Terminate the app if it is still running.
if kill -0 "$APP_PID" 2>/dev/null; then
  kill "$APP_PID" 2>/dev/null || true
  wait "$APP_PID" 2>/dev/null || true
fi

if [ "$FAILED" -ne 0 ]; then
  echo "ERROR: bundle smoke check failed." >&2
  exit 1
fi

echo "Smoke check passed: bundle launched, stayed alive ~3s, no traceback in stderr."
echo "Build complete: $DIST_DIR/todo-md.app"