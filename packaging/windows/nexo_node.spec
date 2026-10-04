# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for NEXO-Node.exe (S13).
# Build: pyinstaller packaging/windows/nexo_node.spec
# Sign release artifacts with signtool (manual channel — no auto-update).

block_cipher = None

a = Analysis(
    ['entry_nexo_node.py'],
    pathex=['../..'],
    binaries=[],
    datas=[],
    hiddenimports=['services.node', 'services.packaging.windows'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['nexo_qa.product'],
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
    name='NEXO-Node',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
