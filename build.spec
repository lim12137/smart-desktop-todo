# -*- mode: python ; coding: utf-8 -*-
"""
待办事项提醒程序 - 多文件打包配置
使用方法: pyinstaller build.spec
"""

import os

block_cipher = None

# 添加必要的隐藏导入
hiddenimports = [
    'babel.numbers',
    'tkcalendar',
    'win10toast',
    'pystray',
    'PIL._tkinter_finder',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'winsound',
    # 确保tkinter相关模块被包含
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext'
]

# 添加资源文件
datas = [
    ('assets', 'assets'),  # 包含整个assets目录
]

# 分析主程序
a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False  # 允许创建多文件格式
)

# 手动添加tkinter DLL文件（如果缺失）
import sys
import glob
if sys.platform == 'win32':
    try:
        tcl_dll_dir = os.path.join(os.path.dirname(sys.executable), 'DLLs')
        if os.path.exists(tcl_dll_dir):
            # 查找tkinter和tcl相关DLL
            for dll_pattern in ['tcl*.dll', 'tk*.dll']:
                for dll_path in glob.glob(os.path.join(tcl_dll_dir, dll_pattern)):
                    if os.path.exists(dll_path):
                        a.binaries.append((os.path.basename(dll_path), dll_path, 'BINARY'))
    except Exception:
        pass

# 创建PYZ归档文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建可执行文件（多文件格式）
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # 不包含二进制文件
    name='待办事项提醒',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.svg' if os.path.exists('assets/icon.svg') else None  # 暂时注释掉，因为SVG格式不被支持
)

# 创建收集器，包含所有依赖文件
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='待办事项提醒'  # 输出目录名称
)
