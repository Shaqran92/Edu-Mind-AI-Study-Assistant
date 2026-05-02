# -*- mode: python ; coding: utf-8 -*-
"""
EduMind PyInstaller Spec File
Builds a single-folder executable with all dependencies.
"""

import os
import sys

block_cipher = None

# Collect all Python source files from the project
a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Data files needed at runtime
        ('.env', '.'),
        ('assets', 'assets'),
        ('prompts.py', '.'),
        ('config.py', '.'),
        ('utils.py', '.'),
        # Include all package directories
        ('core', 'core'),
        ('data', 'data'),
        ('ui', 'ui'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.sip',
        # Google AI
        'google.generativeai',
        'google.ai',
        'google.auth',
        'google.api_core',
        # Science/ML
        'sklearn',
        'sklearn.feature_extraction',
        'sklearn.feature_extraction.text',
        'sklearn.metrics',
        'sklearn.metrics.pairwise',
        'sklearn.utils',
        'sklearn.utils._typedefs',
        'sklearn.utils._heap',
        'sklearn.utils._sorting',
        'sklearn.utils._vector_sentinel',
        'sklearn.neighbors._partition_nodes',
        # PDF
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'reportlab.lib.styles',
        # Other
        'dotenv',
        'requests',
        'sqlite3',
        'json',
        'keyring',
        'keyring.backends',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
        'networkx',
        'PIL',
        'numpy',
        'youtube_transcript_api',
        'defusedxml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'pytest',
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
    name='EduMind',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window — windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EduMind',
)
