#!/usr/bin/env bash
set -euo pipefail

# 桌面后端 PyInstaller 构建脚本（macOS/Linux）
# 关键变化：--onedir 代替 --onefile，安装时一次解压，启动免触发杀软实时扫描，
# 同时把 onefile 自带的压缩/解压开销也节省下来。

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DIST_DIR="$ROOT_DIR/frontend/src-tauri/resources/backend"
BUILD_DIR="$ROOT_DIR/backend/.pyinstaller"
HOOKS_DIR="$BUILD_DIR/hooks"
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

rm -rf "$DIST_DIR" "$BUILD_DIR/build" "$BUILD_DIR/spec"
mkdir -p "$DIST_DIR" "$BUILD_DIR/build" "$BUILD_DIR/spec"
mkdir -p "$STAGED_FONT_DIR"

if [ -f "$FONT_FILE" ]; then
  cp "$FONT_FILE" "$STAGED_FONT_FILE"
fi

PYINSTALLER_ARGS=(
  --noconfirm
  --clean
  # ✨ onedir：安装时一次解压，比 onefile 启动快 5–15×
  --onedir
  --name public_opinion_backend
  --distpath "$DIST_DIR"
  --workpath "$BUILD_DIR/build"
  --specpath "$BUILD_DIR/spec"
  --additional-hooks-dir "$HOOKS_DIR"
  --runtime-hook "$HOOKS_DIR/rthook-snownlp.py"
  # hooks 已经通过 collect_data_files 把 snownlp/jieba/wordcloud 的数据文件
  # 全部拉进来了，再加 --collect-all 只会重复打入，徒增体积。仅显式收集 submodules。
  --collect-submodules snownlp
  --collect-submodules jieba
  --collect-submodules wordcloud
  --hidden-import aiosqlite
  --collect-submodules passlib.handlers
  # 排除明确未使用的重型模块，减小体积
  --exclude-module tkinter
  --exclude-module matplotlib
  --exclude-module scipy
  --exclude-module IPython
  --exclude-module unittest
  --exclude-module pydoc
  --exclude-module test
  --exclude-module tests
  --exclude-module PIL.ImageQt
  --exclude-module PIL.ImageTk
  --exclude-module numpy.tests
)

if [ -f "$STAGED_FONT_FILE" ]; then
  PYINSTALLER_ARGS+=("--add-data" "$STAGED_FONT_FILE:.")
fi

pyinstaller "${PYINSTALLER_ARGS[@]}" "$ENTRY_FILE"

# 验证输出（onedir 模式下 DIST_DIR/public_opinion_backend/ 是一个目录）
BACKEND_BUNDLE_DIR="$DIST_DIR/public_opinion_backend"
BACKEND_BIN="$BACKEND_BUNDLE_DIR/public_opinion_backend"
if [ -f "$BACKEND_BIN" ]; then
  SIZE=$(du -sh "$BACKEND_BUNDLE_DIR" | cut -f1)
  echo "桌面后端已输出到 $BACKEND_BUNDLE_DIR （onedir，整体 $SIZE）"
  chmod +x "$BACKEND_BIN"
else
  echo "构建失败: $BACKEND_BIN 未找到" >&2
  ls -la "$DIST_DIR" || true
  exit 1
fi
