#!/usr/bin/env python3
"""PySide6 form with the Mupen64Plus launch options.

UI-only skeleton: nothing is wired up, no command line is assembled and no
emulator is launched.

Configuration (defaults, ROM folders, joysticks) lives in ``config.toml`` and
is handled by ``config.py``.
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

    # ######################### Folders (no config defaults)
    def build_folders_group(self):
        group = QGroupBox('Folders')

        form = QFormLayout(group)
        form.addRow('N64 ROMs folder', self.build_folder_row('n64_roms_home'))
        form.addRow('GB/GBC ROMs folder', self.build_folder_row('gb_gbc_roms_home'))
        form.addRow('N64 saves folder', self.build_folder_row('n64_saves_home'))
        form.addRow('N64 screenshots folder', self.build_folder_row('n64_screenshots_home'))

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
        if key in ('n64_roms_home', 'gb_gbc_roms_home'):
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

    # ######################### N64 game + controllers
    def build_game_group(self):
        group = QGroupBox('N64 game')

        form = QFormLayout(group)

        self.rom_combo = QComboBox()
        self.fill_rom_combo(self.rom_combo, self.config['n64_roms_home'], '*.?64',
                            '(no N64 ROMs folder set)')
        form.addRow('N64 game', self.rom_combo)

        self.controllers_spin = QSpinBox()
        self.controllers_spin.setRange(1, len(self.config['controllers']['names']))
        self.controllers_spin.setValue(self.config['controllers']['default'])
        form.addRow('Number of controllers', self.controllers_spin)

        return group

    # ######################### controller loop
    def build_controllers_group(self):
        group = QGroupBox('Controllers')

        layout = QVBoxLayout(group)

        tabs = QTabWidget()
        for controller_id in range(1, len(self.config['controllers']['names']) + 1):
            tabs.addTab(
                self.build_controller_tab(),
                'Controller-{}'.format(controller_id))

        layout.addWidget(tabs)

        return group

    def build_controller_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        expansion_combo = QComboBox()
        for pak in self.config['controllers']['expansion_paks']:
            expansion_combo.addItem(pak['label'], pak['id'])
        self.select_combo(expansion_combo, self.config['controllers']['expansion_pak_default'])
        form.addRow('Expansion pak', expansion_combo)

        joystick_combo = QComboBox()
        joysticks = self.config['controllers']['joysticks']['names']
        if joysticks:
            joystick_combo.addItems(joysticks)
        else:
            joystick_combo.addItem('(no configured joysticks)')
            joystick_combo.setEnabled(False)
        self.select_combo(joystick_combo, self.config['controllers']['joysticks']['default'])
        form.addRow('Configured joystick', joystick_combo)

        # Only used by the Transfer pak.
        gb_combo = QComboBox()
        self.gb_combos.append(gb_combo)
        self.fill_rom_combo(gb_combo, self.config['gb_gbc_roms_home'], '*.gb*',
                            '(no GB/GBC ROMs folder set)')
        form.addRow('GB/GBC game', gb_combo)

        hint = QLabel('GB/GBC game is only used with the Transfer pak.')
        hint.setEnabled(False)
        form.addRow(hint)

        return tab

    # ######################### Display and emulation
    def build_display_group(self):
        group = QGroupBox('Display and emulation')

        form = QFormLayout(group)

        self.video_combo = QComboBox()
        self.video_combo.addItems(self.config['graphics']['video_plugins'])
        self.select_combo(self.video_combo, self.config['graphics']['video_plugin_default'])
        form.addRow('Video plugin', self.video_combo)

        resolution = self.config['graphics']['resolution']
        self.resolution_edit = QLineEdit(resolution)
        self.resolution_edit.setPlaceholderText(resolution)
        form.addRow('Resolution', self.resolution_edit)

        self.emulation_mode_combo = QComboBox()
        for mode in self.config['emulation']['modes']:
            self.emulation_mode_combo.addItem(mode['label'], mode['id'])
        self.select_combo(self.emulation_mode_combo, self.config['emulation']['mode_default'])
        form.addRow('Emulation mode', self.emulation_mode_combo)

        return group


def main():
    app = QApplication(argv)

    window = Mupen64PlusForm()
    window.show()

    exit(app.exec())


if __name__ == '__main__':
    main()
