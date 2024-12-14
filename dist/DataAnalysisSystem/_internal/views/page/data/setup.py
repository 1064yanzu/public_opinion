"""
打包配置文件
"""
from setuptools import setup

APP = ['csv_editor.py']
DATA_FILES = [
    ('data', [
        'cases.csv',
        'timelines.csv',
        'analysis.csv',
        'suggestions.csv'
    ])
]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pandas', 'ttkthemes'],
    'iconfile': 'app_icon.icns',  # 如果你有图标文件的话
    'plist': {
        'CFBundleName': '舆情案例数据管理系统',
        'CFBundleDisplayName': '舆情案例数据管理系统',
        'CFBundleIdentifier': 'com.yuqing.csvmanager',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': '© 2024',
    },
    'resources': ['data']
}

setup(
    name='舆情案例数据管理系统',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 