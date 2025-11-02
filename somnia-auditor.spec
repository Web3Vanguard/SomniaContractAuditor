# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Get project paths
project_root = Path(SPECPATH)
src_dir = project_root / 'src'
entry_point = project_root / 'entry_point.py'

a = Analysis(
    [str(entry_point)],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'click',
        'somnia_contract_auditor',
        'somnia_contract_auditor.cli',
        'somnia_contract_auditor.file_discovery',
        'somnia_contract_auditor.slither_runner',
        'somnia_contract_auditor.solhint_runner',
        'somnia_contract_auditor.report_generator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='somnia-auditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

