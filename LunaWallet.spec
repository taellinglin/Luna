# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect everything for critical packages
datas = []
binaries = []
hiddenimports = []

# Collect all data and binaries for requests and urllib3
for package in ['requests', 'urllib3', 'chardet', 'idna', 'certifi']:
    try:
        pkg_data, pkg_binaries, pkg_hidden = collect_all(package)
        datas.extend(pkg_data)
        binaries.extend(pkg_binaries)
        hiddenimports.extend(pkg_hidden)
    except Exception as e:
        print(f"Warning: Could not collect {package}: {e}")

# Additional hidden imports that might be missed
hiddenimports.extend([
    'ssl', '_ssl',
    'cryptography',
    'cryptography.hazmat',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.ciphers',
    'cryptography.hazmat.primitives.kdf',
    'cryptography.hazmat.primitives.serialization',
    'cryptography.x509',
    'OpenSSL',
    'urllib3.contrib.pyopenssl',
    'urllib3.packages.backports',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.base',
    'email.mime.nonmultipart',
    'email.encoders',
    'email.utils',
    'http',
    'http.client',
    'http.cookies',
    'json',
    'base64',
    'hashlib',
    'hmac',
    'secrets',
    'socket',
])

# Collect certificate files specifically
try:
    certifi_data = collect_data_files('certifi')
    datas.extend(certifi_data)
except:
    # Manual fallback for certifi
    import certifi
    cert_path = certifi.where()
    if os.path.exists(cert_path):
        datas.append((cert_path, 'certifi'))

# Add SSL DLLs and binaries
if sys.platform == 'win32':
    # Common paths for SSL libraries
    possible_ssl_paths = [
        # Miniconda/Anaconda paths
        os.path.join(sys.prefix, 'DLLs', '_ssl.pyd'),
        os.path.join(sys.prefix, 'DLLs', '_hashlib.pyd'),
        os.path.join(sys.prefix, 'DLLs', '_ctypes.pyd'),
        os.path.join(sys.prefix, 'Library', 'bin', 'libssl-1_1-x64.dll'),
        os.path.join(sys.prefix, 'Library', 'bin', 'libcrypto-1_1-x64.dll'),
        os.path.join(sys.prefix, 'Library', 'bin', 'libssl-3-x64.dll'),
        os.path.join(sys.prefix, 'Library', 'bin', 'libcrypto-3-x64.dll'),
        # Standard Python paths
        os.path.join(sys.prefix, 'DLLs', 'libssl-1_1-x64.dll'),
        os.path.join(sys.prefix, 'DLLs', 'libcrypto-1_1-x64.dll'),
    ]
    
    for ssl_path in possible_ssl_paths:
        if os.path.exists(ssl_path):
            binaries.append((ssl_path, '.'))

a = Analysis(
    ['luna_wallet.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_ssl.py'],  # SSL runtime hook
    excludes=[
        'tkinter',
        'unittest',
        'pydoc',
        'pystray',
        'PIL',
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
    a.binaries,
    a.datas,
    [],
    name='LunaWallet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Set to False for better debugging
    upx=False,    # Set to False to avoid compression issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep as True for debugging, set to False later
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='wallet_icon.ico' if os.path.exists('wallet_icon.ico') else None,
)