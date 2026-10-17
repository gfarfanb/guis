#!/usr/bin/env python3
"""PySide6 form for scripts/games/.libs/start-mupen64plus.bat.

UI-only skeleton: every interactive ``set /P`` prompt found in the batch
script is mirrored with an appropriate widget.  Nothing is wired up, no
command line is assembled and no emulator is launched.

Original prompts mapped below:
    n64-index>            -> N64 ROM combo box
    num-controllers>      -> Number of controllers spin box
    expansion-pak-num>    -> Expansion pak combo box (per controller)
    joystick-config-index>-> Configured joystick combo box (per controller)
    gc-gbc-index>         -> GB/GBC ROM combo box (per controller)
    gfx-video-index>      -> Video plugin combo box
    resolution>           -> Display resolution line edit
    emumode-index>        -> Emulation mode combo box
"""

from glob import glob
from os import environ
from os.path import basename, isfile, join
from sys import argv, exit, path

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


# ######################### start-mupen64plus.bat defaults
CONTROLLER_NAMES = [
    'Input-SDL-Control1',
    'Input-SDL-Control2',
    'Input-SDL-Control3',
    'Input-SDL-Control4',
]

CONTROLLERS_DEFAULT = 1

# "set "_expansion_paks[<idx>]=<value>|<label>""
EXPANSION_PAKS = [
    ('1', 'None'),
    ('2', 'Mem pak'),
    ('4', 'Transfer pak'),
    ('5', 'Rumble pak'),
]
EXPANSION_PAK_DEFAULT = 'Rumble pak'

GFX_VIDEO_PLUGINS = [
    'mupen64plus-video-glide64mk2',
    'mupen64plus-video-rice',
]
GFX_VIDEO_PLUGIN_DEFAULT = GFX_VIDEO_PLUGINS[0]

RESOLUTION_DEFAULT = '1024x768'

# "set "_emulation_modes[<idx>]=<value>|<label>""
EMULATION_MODES = [
    ('0', 'Pure Interpreter'),
    ('1', 'Cached Interpreter'),
    ('2', 'Dynamic Recompiler'),
]
EMULATION_MODE_DEFAULT = 'Dynamic Recompiler'


# ######################### Environment helpers
def load_env_vars():
    """Best effort import of %PYLIBSPATH%/env_vars (optional)."""
    try:
        path.append(environ.get('PYLIBSPATH', ''))
        import env_vars  # pyright: ignore[reportMissingImports]
        return env_vars
    except Exception:
        return None


ENV_VARS = load_env_vars()


def env_value(name, default=None):
    if ENV_VARS is not None:
        try:
            return ENV_VARS.env_value(name)
        except Exception:
            return default
    return environ.get(name, default)


def list_home_files(home, pattern):
    if not home:
        return []
    return sorted(
        file
        for file in glob(join(home, pattern))
        if isfile(file)
    )


def configured_joysticks():
    """Build the joystick list from N64_JOYSTICK_NAMES[<i>] (1..length)."""
    joysticks = []
    length = env_value('N64_CONFIGURED_JOYSTICK_LENGTH')

    try:
        length = int(length)
    except (TypeError, ValueError):
        length = 0

    for index in range(1, length + 1):
        name = env_value('N64_JOYSTICK_NAMES[{}]'.format(index))
        if name:
            joysticks.append(name)

    return joysticks


# ######################### Widgets
class Mupen64PlusForm(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Mupen64Plus - Launch options')

        content = QWidget()
        layout = QVBoxLayout(content)

        layout.addWidget(self.build_game_group())
        layout.addWidget(self.build_controllers_group())
        layout.addWidget(self.build_display_group())
        layout.addStretch()

        self.setCentralWidget(content)
        self.resize(560, 620)

    # ######################### n64-index> + num-controllers>
    def build_game_group(self):
        group = QGroupBox('N64 game')

        form = QFormLayout(group)

        self.rom_combo = self.build_rom_combo()
        form.addRow('N64 game (n64-index>)', self.rom_combo)

        self.controllers_spin = QSpinBox()
        self.controllers_spin.setRange(1, len(CONTROLLER_NAMES))
        self.controllers_spin.setValue(CONTROLLERS_DEFAULT)
        form.addRow('Number of controllers (num-controllers>)', self.controllers_spin)

        return group

    def build_rom_combo(self):
        combo = QComboBox()
        roms = list_home_files(env_value('N64_ROMS_HOME'), '*.?64')

        if roms:
            for rom in roms:
                combo.addItem(basename(rom), rom)
        else:
            combo.addItem('(N64_ROMS_HOME not found)')
            combo.setEnabled(False)

        return combo

    # ######################### controller loop
    def build_controllers_group(self):
        group = QGroupBox('Controllers')

        layout = QVBoxLayout(group)

        tabs = QTabWidget()
        for controller_id, controller_name in enumerate(CONTROLLER_NAMES, start=1):
            tabs.addTab(
                self.build_controller_tab(controller_id, controller_name),
                'Controller-{}'.format(controller_id))

        layout.addWidget(tabs)

        return group

    def build_controller_tab(self, controller_id, controller_name):
        tab = QWidget()
        form = QFormLayout(tab)

        note = QLabel('Options applied as --set {}[...]'.format(controller_name))
        form.addRow(note)

        # expansion-pak-num>
        expansion_combo = QComboBox()
        for _pak_id, pak_name in EXPANSION_PAKS:
            expansion_combo.addItem(pak_name, _pak_id)
        default_index = expansion_combo.findText(EXPANSION_PAK_DEFAULT)
        if default_index >= 0:
            expansion_combo.setCurrentIndex(default_index)
        form.addRow('Expansion pak (expansion-pak-num>)', expansion_combo)

        # joystick-config-index>
        joystick_combo = QComboBox()
        joysticks = configured_joysticks()
        if joysticks:
            joystick_combo.addItems(joysticks)
        else:
            joystick_combo.addItem('(N64_JOYSTICK_NAMES not set)')
            joystick_combo.setEnabled(False)

        joystick_default = env_value('N64_CONFIGURED_JOYSTICK_DEFAULT')
        try:
            joystick_default = int(joystick_default)
        except (TypeError, ValueError):
            joystick_default = None
        if joystick_default is not None and 1 <= joystick_default <= joystick_combo.count():
            joystick_combo.setCurrentIndex(joystick_default - 1)
        form.addRow('Configured joystick (joystick-config-index>)', joystick_combo)

        # gc-gbc-index> -- only used by the Transfer pak
        gb_combo = QComboBox()
        gb_roms = list_home_files(env_value('GB_GBC_ROMS_HOME'), '*.gb*')
        if gb_roms:
            for rom in gb_roms:
                gb_combo.addItem(basename(rom), rom)
        else:
            gb_combo.addItem('(GB_GBC_ROMS_HOME not found)')
            gb_combo.setEnabled(False)
        form.addRow('GB/GBC game (gc-gbc-index>)', gb_combo)

        hint = QLabel('GB/GBC game is only used with the Transfer pak.')
        hint.setEnabled(False)
        form.addRow(hint)

        return tab

    # ######################### gfx-video-index> + resolution> + emumode-index>
    def build_display_group(self):
        group = QGroupBox('Display and emulation')

        form = QFormLayout(group)

        self.video_combo = QComboBox()
        self.video_combo.addItems(GFX_VIDEO_PLUGINS)
        video_default = self.video_combo.findText(GFX_VIDEO_PLUGIN_DEFAULT)
        if video_default >= 0:
            self.video_combo.setCurrentIndex(video_default)
        form.addRow('Video plugin (gfx-video-index>)', self.video_combo)

        self.resolution_edit = QLineEdit(RESOLUTION_DEFAULT)
        self.resolution_edit.setPlaceholderText(RESOLUTION_DEFAULT)
        form.addRow('Resolution (resolution>)', self.resolution_edit)

        self.emumode_combo = QComboBox()
        for _mode_id, mode_name in EMULATION_MODES:
            self.emumode_combo.addItem(mode_name, _mode_id)
        emumode_default = self.emumode_combo.findText(EMULATION_MODE_DEFAULT)
        if emumode_default >= 0:
            self.emumode_combo.setCurrentIndex(emumode_default)
        form.addRow('Emulation mode (emumode-index>)', self.emumode_combo)

        return group


def main():
    app = QApplication(argv)

    window = Mupen64PlusForm()
    window.show()

    exit(app.exec())


if __name__ == '__main__':
    main()
