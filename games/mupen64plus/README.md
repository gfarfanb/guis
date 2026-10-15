# mupen64plus-gui

A PySide6 launch-options form for the `scripts/games/.libs/start-mupen64plus.bat`
wrapper. Every interactive `set /P` prompt of the batch script is mirrored
with an appropriate widget:

| Batch prompt           | Widget                        |
| ---------------------- | ----------------------------- |
| `n64-index>`           | N64 ROM combo box             |
| `num-controllers>`     | Number of controllers spin box |
| `expansion-pak-num>`   | Expansion pak combo box       |
| `joystick-config-index>` | Configured joystick combo box |
| `gc-gbc-index>`        | GB/GBC ROM combo box          |
| `gfx-video-index>`     | Video plugin combo box        |
| `resolution>`          | Display resolution line edit  |
| `emumode-index>`       | Emulation mode combo box      |

> **Status:** UI-only skeleton. The widgets are not wired to a command line and
> no emulator is launched yet.

## Requirements

- Python 3.9+
- [PySide6](https://pypi.org/project/PySide6/) — GUI toolkit
- [PyInstaller](https://pypi.org/project/pyinstaller/) — standalone builds

## Environment setup

The project uses a local virtual environment in `.venv/`.

### Windows (PowerShell)

```powershell
pwsh -File scripts/setup_env.ps1
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
bash scripts/setup_env.sh
source .venv/bin/activate
```

### Manual setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Execution

Run the GUI directly from the project root:

```bash
python mupen64plus_gui.py
```

Or, after activating the environment, use the installed entry point:

```bash
mupen64plus-gui
```

### Optional environment variables

The form reads these variables when they are present:

| Variable                        | Purpose                                  |
| ------------------------------- | ---------------------------------------- |
| `PYLIBSPATH`                    | Folder containing the shared `env_vars`  |
| `N64_ROMS_HOME`                 | Folder scanned for `*.?64` ROMs          |
| `GB_GBC_ROMS_HOME`              | Folder scanned for `*.gb*` ROMs          |
| `N64_CONFIGURED_JOYSTICK_LENGTH`| Number of configured joysticks           |
| `N64_JOYSTICK_NAMES[i]`         | Name of configured joystick `i`          |
| `N64_CONFIGURED_JOYSTICK_DEFAULT` | Preselected joystick index             |

## Build

Create a standalone executable with PyInstaller.

### Using the scripts

```powershell
# Windows
pwsh -File scripts/build.ps1
```

```bash
# Linux / macOS
bash scripts/build.sh
```

### Manual build

```bash
pyinstaller mupen64plus_gui.spec
# or, without the spec file:
pyinstaller --onefile --windowed --name mupen64plus_gui mupen64plus_gui.py
```

The executable is written to:

- Windows: `dist/mupen64plus_gui.exe`
- Linux / macOS: `dist/mupen64plus_gui`

## Project layout

```
games/mupen64plus/
├── mupen64plus_gui.py       # GUI entry point
├── mupen64plus_gui.spec     # PyInstaller build recipe
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Runtime + build dependencies
├── README.md
├── .gitignore
└── scripts/
    ├── setup_env.ps1 / .sh  # Create venv + install dependencies
    └── build.ps1 / .sh      # PyInstaller build
```
