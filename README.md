# rotom_cam_rpc

## Package as a Windows EXE
1) Install dependencies in a Windows Python environment (3.10+ recommended), including PyInstaller:
   - `pip install pyinstaller` plus any libraries this app needs (Pillow, numpy, opencv-python, keyboard, pypresence, etc.).
2) From the repo root, build a one-file, no-console executable that bundles the assets folder and icon:
   - `pyinstaller --onefile --noconsole --name "XIII Auto Counter" --add-data "assets;assets" --icon assets/rotom/main/main_icon.ico RotomCamRPC_vBeta.0.13.py`
3) The generated exe will be under `dist/` (e.g., `dist/XIII Auto Counter.exe`). Keep the bundled `assets` directory structure intact; `resource_path` will load files from the packaged data.
