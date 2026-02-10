# rotom_cam_rpc

## Package as a Windows EXE
1) Install dependencies in a Windows Python environment (3.10+ recommended), including PyInstaller:
   - `pip install pyinstaller` plus any libraries this app needs (Pillow, numpy, opencv-python, keyboard, pypresence, etc.).
2) From the repo root, build a one-file, no-console executable that bundles the assets folder and icon:
   - `pyinstaller --onefile --noconsole --name "XIII Auto Counter" --add-data "assets;assets" --icon assets/rotom/main/main_icon.ico RotomCamRPC_vBeta.0.13.py`
3) The generated exe will be under `dist/` (e.g., `dist/XIII Auto Counter.exe`). Keep the bundled `assets` directory structure intact; `resource_path` will load files from the packaged data.

**If you see “No module named pyinstaller” even after installing it:**
- Ensure you are using the same Python where you installed PyInstaller: `python -m pip install pyinstaller` then run `python -m PyInstaller ...`.
- Verify your PATH isn’t mixing `python`/`pip` from different environments (e.g., virtualenv vs system). Running `python -m pip show pyinstaller` should report the install location you expect.
- On Windows/PowerShell, the safest invocation is: `python -m PyInstaller --onefile --noconsole --name "XIII Auto Counter" --add-data "assets;assets" --icon assets/rotom/main/main_icon.ico RotomCamRPC_vBeta.0.13.py` (note the capital `P`).
