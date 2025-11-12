# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('templates', 'templates'), ('static', 'static'), ('views', 'views'), ('config', 'config'), ('model', 'model'), ('utils', 'utils'), ('persistent_data', 'persistent_data'), ('spiders', 'spiders'), ('*.csv', '.'), ('E:\\python\\yuqing\\.venv\\Scripts\\..\\Lib\\site-packages\\setuptools\\_vendor\\jaraco\\text\\Lorem ipsum.txt', 'setuptools/_vendor/jaraco/text/')]
binaries = []
hiddenimports = ['flask', 'werkzeug', 'jinja2', 'pandas', 'numpy', 'snownlp', 'jieba', 'wordcloud', 'pyecharts', 'sqlalchemy', 'pymysql', 'amqp', 'multiprocessing', 'bs4', 'requests', 'jsonpath-ng', 'click', 'itsdangerous', 'markupsafe', 'setuptools', 'pkg_resources', 'pathlib']
tmp_ret = collect_all('flask')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('werkzeug')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('jinja2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sqlalchemy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('snownlp')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pyecharts')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('setuptools')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DataAnalysisSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DataAnalysisSystem',
)
