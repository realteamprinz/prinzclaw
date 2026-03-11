# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for prinzclaw macOS .app bundle."""

import os
import sys

block_cipher = None

project_root = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

a = Analysis(
    [os.path.join(project_root, 'macos', 'app.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'macos', 'dashboard'), 'dashboard'),
        (os.path.join(project_root, 'macos', 'resources'), 'resources'),
        (os.path.join(project_root, 'prompts'), 'prompts'),
        (os.path.join(project_root, 'prinzclaw.example.yaml'), '.'),
    ],
    hiddenimports=[
        'rumps',
        'aiohttp',
        'aiohttp.web',
        'yaml',
        'httpx',
        'src',
        'src.config',
        'src.models',
        'src.utils',
        'src.database',
        'src.scanner',
        'src.analyzer',
        'src.crafter',
        'src.publisher',
        'src.gateway',
        'macos',
        'macos.paths',
        'macos.keychain',
        'macos.gateway_mac',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'xmlrpc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='prinzclaw',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # Build for native arch; use 'universal2' with fat-binary deps
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='prinzclaw',
)

app = BUNDLE(
    coll,
    name='prinzclaw.app',
    icon=os.path.join(project_root, 'macos', 'resources', 'app_icon.png'),
    bundle_identifier='ai.prinzit.prinzclaw',
    info_plist={
        'CFBundleName': 'prinzclaw',
        'CFBundleDisplayName': 'prinzclaw',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'ai.prinzit.prinzclaw',
        'LSMinimumSystemVersion': '13.0',
        'LSUIElement': True,  # Menubar app (no dock icon)
        'NSHighResolutionCapable': True,
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'NSHumanReadableCopyright': 'Copyright (c) 2026 Louie Grant Prinz. MIT License.',
    },
)
