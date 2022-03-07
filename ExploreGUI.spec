# -*- mode: python ; coding: utf-8 -*-
from os import path
import sys
import pylsl
from distutils.sysconfig import get_python_lib

if sys.platform == "darwin":
    icon_path = "./installer/ExploreGuiInstaller/ExploreGUI/packages/com.Mentalab.ExploreGUI/extras/MentalabLogo.icns"
else:
    icon_path = "./installer/ExploreGuiInstaller/ExploreGUI/packages/com.Mentalab.ExploreGUI/extras/MentalabLogo.ico"

block_cipher = None
main_path = path.join('exploregui', 'main.py')

a = Analysis([main_path],
             pathex=[get_python_lib()],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
a.datas += Tree(path.dirname(pylsl.__file__), prefix='pylsl', excludes='__pycache__')
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='ExploreGUI',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon=icon_path)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ExploreGUI')

if sys.platform == 'darwin':
    app = BUNDLE(coll,
                 name='ExploreGUI.app',
                 icon=icon_path,
                 bundle_identifier='com.mentalab.exploregui',
                 version='0.2.0',
                 info_plist={
                  'NSPrincipalClass': 'NSApplication',
                  'NSAppleScriptEnabled': False,
                  'NSHighResolutionCapable': True,
                  'LSBackgroundOnly': False,
                  'NSBluetoothPeripheralUsageDescription': 'ExploreGUI uses Bluetooth to communicate with the Explore devices.'
                 })