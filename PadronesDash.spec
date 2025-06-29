# PadronesDash.spec
# ---------------------------------------------------------------------
block_cipher = None

from PyInstaller.utils.hooks import collect_submodules
dash_submods = collect_submodules("dash")
dext_submods = collect_submodules("dash_extensions")

extra_hidden = (
    dash_submods +
    dext_submods +
    ["dash.long_callback", "dash.development.base_component"]
)
# ---------------------------------------------------------------------python -m pip install "dash[diskcache]==2.14.2" "dash-extensions==1.0.9"


import os
project_path = r"C:\Users\Lionel\Desktop\Desarrollos\Python\app"

a = Analysis(
    ["app.py"],
    pathex=[project_path],
    binaries=[],
    datas=[
        (os.path.join(project_path, "referencias"), "referencias"),
        (os.path.join(project_path, "assets"),      "assets"),
    ],
    hiddenimports=extra_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PadronesDash",
    debug=True,                  # ← activa trazas completas
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                   # ponelo en False si no tenés UPX
    console=True,                # ← cambiá a True para ver la consola
    disable_windowed_traceback=False,
)

