#!/usr/bin/env bash
set -euo pipefail

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

# 获取各 NLP 库的安装路径（用于显式 --add-data）
SNOWNLP_PATH=$(python -c "import snownlp, os; print(os.path.dirname(snownlp.__file__))")
echo "snownlp path: $SNOWNLP_PATH"

PYINSTALLER_ARGS=(
  --noconfirm
  --clean
  --onefile
  --name public_opinion_backend
  --distpath "$DIST_DIR"
  --workpath "$BUILD_DIR/build"
  --specpath "$BUILD_DIR/spec"
  # 使用自定义 hooks 目录（修复 snownlp/jieba/wordcloud 数据文件问题）
  --additional-hooks-dir "$HOOKS_DIR"
  # snownlp runtime hook（确保 frozen 环境路径正确）
  --runtime-hook "$HOOKS_DIR/rthook-snownlp.py"
  # 显式收集 NLP 库所有子模块和数据文件
  --collect-all snownlp
  --collect-all jieba
  --collect-all wordcloud
  # 显式 add-data snownlp 数据文件（双重保险，macOS 用 : 分隔符）
  "--add-data" "${SNOWNLP_PATH}/normal/stopwords.txt:snownlp/normal/"
  "--add-data" "${SNOWNLP_PATH}/normal/pinyin.txt:snownlp/normal/"
  "--add-data" "${SNOWNLP_PATH}/seg/data.txt:snownlp/seg/"
  "--add-data" "${SNOWNLP_PATH}/seg/seg.marshal:snownlp/seg/"
  "--add-data" "${SNOWNLP_PATH}/seg/seg.marshal.3:snownlp/seg/"
  "--add-data" "${SNOWNLP_PATH}/sentiment/neg.txt:snownlp/sentiment/"
  "--add-data" "${SNOWNLP_PATH}/sentiment/pos.txt:snownlp/sentiment/"
  "--add-data" "${SNOWNLP_PATH}/sentiment/sentiment.marshal:snownlp/sentiment/"
  "--add-data" "${SNOWNLP_PATH}/sentiment/sentiment.marshal.3:snownlp/sentiment/"
  "--add-data" "${SNOWNLP_PATH}/tag/199801.txt:snownlp/tag/"
  "--add-data" "${SNOWNLP_PATH}/tag/tag.marshal:snownlp/tag/"
  "--add-data" "${SNOWNLP_PATH}/tag/tag.marshal.3:snownlp/tag/"
  # 其他 hidden imports
  --hidden-import aiosqlite
  --collect-submodules passlib.handlers
)

if [ -f "$STAGED_FONT_FILE" ]; then
  PYINSTALLER_ARGS+=("--add-data" "$STAGED_FONT_FILE:.")
fi

pyinstaller "${PYINSTALLER_ARGS[@]}" "$ENTRY_FILE"

echo "桌面后端已输出到 $DIST_DIR"
