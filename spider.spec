# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['spider.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('factory', 'factory'),
        ('action', 'action'),
        ('monitor.py', '.'),
        ('database.py', '.'),
        ('models.py', '.'),
        ('utils.py', '.'),
        ('dt_wecom_key.config', '.'),
        ],
    hiddenimports=['pyodbc', 'json', 'psutil', 'requests'],
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
    name='spider',
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
