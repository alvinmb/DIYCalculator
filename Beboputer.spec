# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bin\\run_beboputer_v7.py'],
    pathex=['bin'],
    binaries=[],
    datas=[
        ('BITMAPS', 'BITMAPS'),
        ('Config', 'Config'),
        ('Data', 'Data'),
        ('WorkInProgress', 'WorkInProgress'),
        ('databook', 'databook'),
        ('tutorial', 'tutorial'),
        ('bin\\beboputer_v7_help.html', '.'),
    ],
    hiddenimports=[],
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
    name='Beboputer',
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
    name='Beboputer',
)
