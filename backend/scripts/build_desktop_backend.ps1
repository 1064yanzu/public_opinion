#Requires -Version 5.1
<#
.SYNOPSIS
    构建桌面后端 PyInstaller 二进制 (Windows)
.DESCRIPTION
    采用 --onedir 模式：NSIS 安装时一次性解压，运行时不再触发杀软实时扫描，
    冷启动从 30-60 秒压缩到 3-8 秒。
    输出到 frontend/src-tauri/resources/backend/public_opinion_backend/
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

# ===== 查找 MSVC 运行时 DLL =====
$pythonDir = python -c "import sys; print(sys.prefix)"
$crtDlls = @("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll")
$crtArgs = @()

# System32（64位）和 SysWOW64（32位）都要查，覆盖所有干净的 Windows
$searchRoots = @(
    $pythonDir,
    (Join-Path $env:SystemRoot "System32"),
    (Join-Path $env:SystemRoot "SysWOW64")
)

foreach ($dll in $crtDlls) {
    $found = $false
    foreach ($root in $searchRoots) {
        $dllPath = Join-Path $root $dll
        if (Test-Path $dllPath) {
            Write-Host "Found CRT DLL: $dllPath"
            $crtArgs += @("--add-binary", "${dllPath};.")
            $found = $true
            break
        }
    }
    if (-not $found) {
        Write-Warning "CRT DLL not found in any search root: $dll"
    }
}

# 构建参数
$pyinstallerArgs = @(
    "--noconfirm",
    "--clean",
    # ✨ onedir：杀软友好，启动快
    "--onedir",
    "--name", "public_opinion_backend",
    "--distpath", $DIST_DIR,
    "--workpath", (Join-Path $BUILD_DIR "build"),
    "--specpath", (Join-Path $BUILD_DIR "spec"),
    "--win-private-assemblies",
    "--win-no-prefer-redirects",
    "--additional-hooks-dir", $HOOKS_DIR,
    "--runtime-hook", (Join-Path $HOOKS_DIR "rthook-snownlp.py"),
    # hooks 已经收集了 snownlp/jieba/wordcloud 的数据文件，仅显式 submodules
    "--collect-submodules", "snownlp",
    "--collect-submodules", "jieba",
    "--collect-submodules", "wordcloud",
    "--hidden-import", "aiosqlite",
    "--collect-submodules", "passlib.handlers",
    "--exclude-module", "tkinter",
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy",
    "--exclude-module", "IPython",
    "--exclude-module", "unittest",
    "--exclude-module", "pydoc",
    "--exclude-module", "test",
    "--exclude-module", "tests",
    "--exclude-module", "PIL.ImageQt",
    "--exclude-module", "PIL.ImageTk",
    "--exclude-module", "numpy.tests"
)

# 追加 CRT DLL
$pyinstallerArgs += $crtArgs

# 追加字体
if (Test-Path $STAGED_FONT_FILE) {
    $pyinstallerArgs += @("--add-data", "${STAGED_FONT_FILE};.")
}

$pyinstallerArgs += $ENTRY_FILE

Write-Host "Running pyinstaller (onedir mode)..."
& pyinstaller @pyinstallerArgs

# onedir 模式下结果是 DIST_DIR/public_opinion_backend/public_opinion_backend.exe
$backendBundleDir = Join-Path $DIST_DIR "public_opinion_backend"
$backendExe = Join-Path $backendBundleDir "public_opinion_backend.exe"
if (Test-Path $backendExe) {
    $bundleSize = (Get-ChildItem -Recurse $backendBundleDir | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "桌面后端已输出到 $backendBundleDir（onedir，整体 $([math]::Round($bundleSize, 1)) MB）" -ForegroundColor Green
} else {
    Write-Error "构建失败: $backendExe 未找到"
    exit 1
}
