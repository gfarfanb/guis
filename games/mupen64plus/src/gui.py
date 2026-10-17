#!/usr/bin/env python3
"""PySide6 form for scripts/games/.libs/start-mupen64plus.bat.

UI-only skeleton: every interactive ``set /P`` prompt found in the batch
script is mirrored with an appropriate widget.  Nothing is wired up, no
command line is assembled and no emulator is launched.

Configuration (defaults, ROM folders, joysticks) lives in ``config.toml`` and
is handled by ``config.py``.

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
from os.path import basename, isfile, join
from sys import argv, exit

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config import load_config, save_config


def list_home_files(home, pattern):
    if not home:
        return []
    return sorted(
        file
        for file in glob(join(home, pattern))
        if isfile(file)
    )


# ######################### Widgets
class Mupen64PlusForm(QMainWindow):

    def __init__(self):
        super().__init__()

        self.config = load_config()
        self.gb_combos = []

        self.setWindowTitle('Mupen64Plus - Launch options')

        content = QWidget()
        layout = QVBoxLayout(content)

        layout.addWidget(self.build_folders_group())
        layout.addWidget(self.build_game_group())
        layout.addWidget(self.build_controllers_group())
        layout.addWidget(self.build_display_group())
        layout.addStretch()

        self.setCentralWidget(content)
        self.resize(560, 660)

    # ######################### ROM folders (no config defaults)
    def build_folders_group(self):
        group = QGroupBox('ROM folders')

        form = QFormLayout(group)
        form.addRow('N64 ROMs folder (n64_roms_home)', self.build_folder_row('n64_roms_home'))
        form.addRow('GB/GBC ROMs folder (gb_gbc_roms_home)', self.build_folder_row('gb_gbc_roms_home'))

        return group

    def build_folder_row(self, key):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        edit = QLineEdit(self.config[key])
        edit.setReadOnly(True)

        button = QPushButton('Browse...')
        button.clicked.connect(lambda: self.choose_folder(key, edit))

        layout.addWidget(edit)
        layout.addWidget(button)

        return row

    def choose_folder(self, key, edit):
        folder = QFileDialog.getExistingDirectory(self, 'Select folder', self.config[key])
        if not folder:
            return

        self.config[key] = folder
        edit.setText(folder)
        save_config(self.config)
        self.refresh_rom_combos()

    def refresh_rom_combos(self):
        self.fill_rom_combo(self.rom_combo, self.config['n64_roms_home'], '*.?64',
                            '(no N64 ROMs folder set)')
        for combo in self.gb_combos:
            self.fill_rom_combo(combo, self.config['gb_gbc_roms_home'], '*.gb*',
                                '(no GB/GBC ROMs folder set)')

    @staticmethod
    def fill_rom_combo(combo, home, pattern, missing_label):
        combo.clear()
        roms = list_home_files(home, pattern)

        if roms:
            for rom in roms:
                combo.addItem(basename(rom), rom)
            combo.setEnabled(True)
        else:
            combo.addItem(missing_label)
            combo.setEnabled(False)

    @staticmethod
    def select_combo(combo, text):
        index = combo.findText(str(text))
        if index >= 0:
            combo.setCurrentIndex(index)

    # ######################### n64-index> + num-controllers>
    def build_game_group(self):
        group = QGroupBox('N64 game')

        form = QFormLayout(group)

        self.rom_combo = QComboBox()
        self.fill_rom_combo(self.rom_combo, self.config['n64_roms_home'], '*.?64',
                            '(no N64 ROMs folder set)')
        form.addRow('N64 game (n64-index>)', self.rom_combo)

        self.controllers_spin = QSpinBox()
        self.controllers_spin.setRange(1, len(self.config['controller_names']))
        self.controllers_spin.setValue(self.config['controllers_default'])
        form.addRow('Number of controllers (num-controllers>)', self.controllers_spin)

        return group

    # ######################### controller loop
    def build_controllers_group(self):
        group = QGroupBox('Controllers')

        layout = QVBoxLayout(group)

        tabs = QTabWidget()
        for controller_id, controller_name in enumerate(self.config['controller_names'], start=1):
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
        for _pak_id, pak_name in self.config['expansion_paks']:
            expansion_combo.addItem(pak_name, _pak_id)
        self.select_combo(expansion_combo, self.config['expansion_pak_default'])
        form.addRow('Expansion pak (expansion-pak-num>)', expansion_combo)

        # joystick-config-index>
        joystick_combo = QComboBox()
        joysticks = self.config['configured_joystick_names']
        if joysticks:
            joystick_combo.addItems(joysticks)
        else:
            joystick_combo.addItem('(no configured joysticks)')
            joystick_combo.setEnabled(False)
        self.select_combo(joystick_combo, self.config['configured_joystick_default'])
        form.addRow('Configured joystick (joystick-config-index>)', joystick_combo)

        # gc-gbc-index> -- only used by the Transfer pak
        gb_combo = QComboBox()
        self.gb_combos.append(gb_combo)
        self.fill_rom_combo(gb_combo, self.config['gb_gbc_roms_home'], '*.gb*',
                            '(no GB/GBC ROMs folder set)')
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
        self.video_combo.addItems(self.config['gfx_video_plugins'])
        self.select_combo(self.video_combo, self.config['gfx_video_plugin_default'])
        form.addRow('Video plugin (gfx-video-index>)', self.video_combo)

        resolution = self.config['resolution_default']
        self.resolution_edit = QLineEdit(resolution)
        self.resolution_edit.setPlaceholderText(resolution)
        form.addRow('Resolution (resolution>)', self.resolution_edit)

        self.emumode_combo = QComboBox()
        for _mode_id, mode_name in self.config['emulation_modes']:
            self.emumode_combo.addItem(mode_name, _mode_id)
        self.select_combo(self.emumode_combo, self.config['emulation_mode_default'])
        form.addRow('Emulation mode (emumode-index>)', self.emumode_combo)

        return group


def main():
    app = QApplication(argv)

    window = Mupen64PlusForm()
    window.show()

    exit(app.exec())


if __name__ == '__main__':
    main()
