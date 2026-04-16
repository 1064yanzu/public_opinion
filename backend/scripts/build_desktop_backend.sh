#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DIST_DIR="$ROOT_DIR/frontend/src-tauri/resources/backend"
BUILD_DIR="$ROOT_DIR/backend/.pyinstaller"
ENTRY_FILE="$ROOT_DIR/backend/run_desktop.py"
FONT_FILE="$ROOT_DIR/三极泼墨体.ttf"
STAGED_FONT_DIR="$BUILD_DIR/assets"
STAGED_FONT_FILE="$STAGED_FONT_DIR/sanjipomoti.ttf"

if [ ! -d "$ROOT_DIR/.venv" ]; then
  echo "缺少根目录 .venv，请先创建虚拟环境。"
  exit 1
fi

source "$ROOT_DIR/.venv/bin/activate"
python -m pip install --quiet pyinstaller

rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$STAGED_FONT_DIR"

if [ -f "$FONT_FILE" ]; then
  cp "$FONT_FILE" "$STAGED_FONT_FILE"
fi

PYINSTALLER_ARGS=(
  --noconfirm
  --clean
  --onedir
  --name public_opinion_backend
  --distpath "$DIST_DIR"
  --workpath "$BUILD_DIR/build"
  --specpath "$BUILD_DIR/spec"
  --hidden-import aiosqlite
  --collect-submodules passlib.handlers
)

if [ -f "$STAGED_FONT_FILE" ]; then
  PYINSTALLER_ARGS+=(--add-data "$STAGED_FONT_FILE:.")
fi

pyinstaller "${PYINSTALLER_ARGS[@]}" "$ENTRY_FILE"

echo "桌面后端已输出到 $DIST_DIR"
