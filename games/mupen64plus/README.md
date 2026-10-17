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

- Python 3.11+
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

### VS Code env setup

- Select interpreter
    - `Ctrl+P / Python: Select Interpreter / <select_ workspace_project> / <select_env_folder>`

## Execution

Run the GUI directly from the project root:

```bash
python src/gui.py
```

Or, after activating the environment, use the installed entry point:

```bash
mupen64plus-gui
```

## Configuration

All settings live in a `config.toml` file that `config.py` generates on first
run, next to the script (`src/`) or next to the built executable. Its initial
contents come from the committed `src/default_config.toml`, which is where the
shipped defaults are maintained. It replaces the `start-mupen64plus.bat`
environment variables:

| Key                                          | Purpose                                            |
| -------------------------------------------- | -------------------------------------------------- |
| `mupen64plus_home`                           | Folder with the `mupen64plus-ui-console` binaries (no default) |
| `n64_roms_home`                              | Folder scanned for `*.?64` ROMs (no default)       |
| `gb_gbc_roms_home`                           | Folder scanned for `*.gb*` ROMs (no default)       |
| `n64_saves_home`                             | N64 save (SRAM) folder (no default)                |
| `n64_screenshots_home`                       | N64 screenshot folder (no default)                 |
| `controllers.names`                          | `--set` controller names                           |
| `controllers.default`                        | Default number of controllers                      |
| `controllers.expansion_paks` (`[[...]]`)     | `id`, `label` entries                              |
| `controllers.expansion_pak_default`          | Preselected expansion pak label                    |
| `controllers.joysticks.names`                | Configured joysticks (was `N64_JOYSTICK_NAMES[i]`) |
| `controllers.joysticks.default`              | Preselected joystick (default `Keyboard`)          |
| `graphics.video_plugins`                     | Video plugin names                                 |
| `graphics.video_plugin_default`              | Preselected video plugin                           |
| `graphics.resolution`                        | Default display resolution                         |
| `emulation.modes` (`[[...]]`)                | `id`, `label` entries                              |
| `emulation.mode_default`                     | Preselected emulation mode label                   |
| `parameters.types`                           | Type names accepted in ROM profiles and the parameters widget |

The `*_home` folders have no default; pick them with the **Browse...** buttons
in the GUI and they are saved back to `config.toml`.
Settings are grouped into `[controllers]`, `[graphics]` and `[emulation]`
tables, with list-of-pairs written as `[[table]]` arrays of tables.

## ROM profiles

`profile.py` generates `profiles.toml` on first run, seeded from the committed
`src/default_profiles.toml`, and loads per-game **Core/Plugin parameters** for
the selected ROM, so they can be reused in the *Core/Plugin parameters* widget. Profiles are keyed by ROM file name **without
extension**, so both `Banjo-Kazooie.n64` and `Banjo-Kazooie.z64` match
`games.Banjo-Kazooie`.

```toml
[[games.Banjo-Kazooie]]
type = "Core"
name = "DisableExtraMem"
value = "True"
```

Each game holds only `type`/`name`/`value` rows; the `type` must be one of the
`parameters.types` in `config.toml`, otherwise the row is ignored. Selecting a
ROM loads its rows into the *Core/Plugin parameters* widget, and editing the
rows saves them back to the ROM's profile (on ROM change or window close).

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
pyinstaller --onefile --windowed --name mupen64plus_gui src/gui.py
```

The executable is written to:

- Windows: `dist/mupen64plus_gui.exe`
- Linux / macOS: `dist/mupen64plus_gui`

## Project layout

```
games/mupen64plus/
├── src/
│   ├── gui.py               # GUI entry point
│   ├── config.py            # config.toml handling
│   ├── profile.py           # profiles.toml handling (per-ROM parameters)
│   ├── default_config.toml  # committed default config
│   └── default_profiles.toml # committed default ROM profiles
├── config.toml              # generated on first run (git-ignored)
├── profiles.toml            # generated on first run (git-ignored)
├── mupen64plus_gui.spec     # PyInstaller build recipe
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Runtime + build dependencies
├── README.md
├── .gitignore
└── scripts/
    ├── setup_env.ps1 / .sh  # Create venv + install dependencies
    └── build.ps1 / .sh      # PyInstaller build
```
