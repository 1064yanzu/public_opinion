#Requires -Version 5.1
<#
.SYNOPSIS
    构建桌面后端 PyInstaller 二进制 (Windows)
.DESCRIPTION
    等效于 build_desktop_backend.sh 的 Windows PowerShell 版本。
    输出到 frontend/src-tauri/resources/backend/public_opinion_backend.exe
#>
param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$ROOT_DIR = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
$DIST_DIR = Join-Path $ROOT_DIR "frontend\src-tauri\resources\backend"
$BUILD_DIR = Join-Path $ROOT_DIR "backend\.pyinstaller"
$HOOKS_DIR = Join-Path $BUILD_DIR "hooks"
$ENTRY_FILE = Join-Path $ROOT_DIR "backend\run_desktop.py"
$FONT_FILE = Join-Path $ROOT_DIR "三极泼墨体.ttf"
$STAGED_FONT_DIR = Join-Path $BUILD_DIR "assets"
$STAGED_FONT_FILE = Join-Path $STAGED_FONT_DIR "sanjipomoti.ttf"

# 检查虚拟环境
$venvActivate = Join-Path $ROOT_DIR ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Error "缺少根目录 .venv，请先运行: python -m venv .venv"
    exit 1
}

. $venvActivate
python -m pip install --quiet pyinstaller

# 清理
if ($Clean) {
    Remove-Item -Recurse -Force $DIST_DIR -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $BUILD_DIR "build") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $BUILD_DIR "spec") -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $DIST_DIR | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BUILD_DIR "build") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BUILD_DIR "spec") | Out-Null
New-Item -ItemType Directory -Force -Path $STAGED_FONT_DIR | Out-Null

# 复制字体
if (Test-Path $FONT_FILE) {
    Copy-Item $FONT_FILE $STAGED_FONT_FILE -Force
}

# 获取 snownlp 安装路径
$snownlpPath = python -c "import snownlp, os; print(os.path.dirname(snownlp.__file__))"
Write-Host "snownlp path: $snownlpPath"

# ===== 查找 MSVC 运行时 DLL =====
$pythonDir = python -c "import sys; print(sys.prefix)"
$crtDlls = @("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll")
$crtArgs = @()

foreach ($dll in $crtDlls) {
    $dllPath = Join-Path $pythonDir $dll
    if (Test-Path $dllPath) {
        Write-Host "Found CRT DLL: $dllPath"
        $crtArgs += @("--add-binary", "${dllPath};.")
    } else {
        $sysPath = Join-Path $env:SystemRoot "System32" $dll
        if (Test-Path $sysPath) {
            Write-Host "Found CRT DLL (system): $sysPath"
            $crtArgs += @("--add-binary", "${sysPath};.")
        } else {
            Write-Warning "CRT DLL not found: $dll"
        }
    }
}

# 构建参数
$pyinstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--onefile",
    "--name", "public_opinion_backend",
    "--distpath", $DIST_DIR,
    "--workpath", (Join-Path $BUILD_DIR "build"),
    "--specpath", (Join-Path $BUILD_DIR "spec"),
    "--win-private-assemblies",
    "--win-no-prefer-redirects",
    "--additional-hooks-dir", $HOOKS_DIR,
    "--runtime-hook", (Join-Path $HOOKS_DIR "rthook-snownlp.py"),
    "--collect-all", "snownlp",
    "--collect-all", "jieba",
    "--collect-all", "wordcloud",
    "--add-data", "${snownlpPath}/normal/stopwords.txt;snownlp/normal/",
    "--add-data", "${snownlpPath}/normal/pinyin.txt;snownlp/normal/",
    "--add-data", "${snownlpPath}/seg/data.txt;snownlp/seg/",
    "--add-data", "${snownlpPath}/seg/seg.marshal;snownlp/seg/",
    "--add-data", "${snownlpPath}/seg/seg.marshal.3;snownlp/seg/",
    "--add-data", "${snownlpPath}/sentiment/neg.txt;snownlp/sentiment/",
    "--add-data", "${snownlpPath}/sentiment/pos.txt;snownlp/sentiment/",
    "--add-data", "${snownlpPath}/sentiment/sentiment.marshal;snownlp/sentiment/",
    "--add-data", "${snownlpPath}/sentiment/sentiment.marshal.3;snownlp/sentiment/",
    "--add-data", "${snownlpPath}/tag/199801.txt;snownlp/tag/",
    "--add-data", "${snownlpPath}/tag/tag.marshal;snownlp/tag/",
    "--add-data", "${snownlpPath}/tag/tag.marshal.3;snownlp/tag/",
    "--hidden-import", "aiosqlite",
    "--collect-submodules", "passlib.handlers",
    "--exclude-module", "tkinter",
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy"
)

# 追加 CRT DLL
$pyinstallerArgs += $crtArgs

# 追加字体
if (Test-Path $STAGED_FONT_FILE) {
    $pyinstallerArgs += @("--add-data", "${STAGED_FONT_FILE};.")
}

$pyinstallerArgs += $ENTRY_FILE

Write-Host "Running pyinstaller..."
& pyinstaller @pyinstallerArgs

$backendExe = Join-Path $DIST_DIR "public_opinion_backend.exe"
if (Test-Path $backendExe) {
    $size = [math]::Round((Get-Item $backendExe).Length / 1MB, 1)
    Write-Host "桌面后端已输出到 $DIST_DIR ($size MB)" -ForegroundColor Green
} else {
    Write-Error "构建失败: $backendExe 未找到"
    exit 1
}
