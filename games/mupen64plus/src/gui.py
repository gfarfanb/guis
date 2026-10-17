#!/usr/bin/env python3
"""PySide6 form with the Mupen64Plus launch options.

**Execute** collects the Games-tab widgets into a ``Mupen64Plus`` command
(``mupen.py``) and launches ``mupen64plus-ui-console``.

Configuration (defaults, ROM folders, joysticks) lives in ``config.toml`` and
is handled by ``config.py``.
"""

import subprocess
from glob import glob
from os.path import basename, isfile, join
from sys import argv, exit

from PySide6.QtCore import QEvent, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

PARAMETER_NONE = 'None'

CORE_PARAMETERS_URL = 'https://mupen64plus.org/wiki/index.php?title=Mupen64Plus_Core_Parameters'
PLUGIN_PARAMETERS_URL = 'https://mupen64plus.org/wiki/index.php?title=Mupen64Plus_Plugin_Parameters'

from config import load_config, save_config
from mupen import Mupen64Plus
from profile import Profile


def list_home_files(home, pattern):
    if not home:
        return []
    return sorted(
        file
        for file in glob(join(home, pattern))
        if isfile(file)
    )


class ParameterTable(QWidget):
    """Type/Name/Value rows; Enter anywhere or Tab past the last field adds a row."""

    def __init__(self, types):
        super().__init__()

        self.types = [PARAMETER_NONE] + list(types)
        self.rows = []
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setColumnStretch(2, 1)
        self.grid.setColumnStretch(3, 1)
        for column, title in enumerate(('', 'Type', 'Name', 'Value')):
            self.grid.addWidget(QLabel(title), 0, column)

        self.add_row()

    def add_row(self, parameter=None):
        entry = {
            'remove': QPushButton('\u2715'),
            'type': QComboBox(),
            'name': QLineEdit(),
            'value': QLineEdit(),
        }
        entry['remove'].setFixedWidth(28)
        entry['remove'].setToolTip('Delete row')
        entry['remove'].clicked.connect(lambda: self.remove_row(entry))
        entry['type'].addItems(self.types)
        if parameter:
            entry['type'].setCurrentText(parameter['type'])
            entry['name'].setText(parameter['name'])
            entry['value'].setText(parameter.get('value', ''))
        for widget in (entry['type'], entry['name'], entry['value']):
            widget.installEventFilter(self)

        self.rows.append(entry)
        self.relayout()

        return entry

    def remove_row(self, entry):
        self.drop_row(entry)

        if self.rows:
            self.relayout()
        else:
            self.add_row()

    def drop_row(self, entry):
        for widget in entry.values():
            widget.setParent(None)
            widget.deleteLater()
        self.rows.remove(entry)

    def set_parameters(self, parameters):
        """Replace all rows with ``parameters`` (type/name/value dicts)."""
        for entry in list(self.rows):
            self.drop_row(entry)
        for parameter in parameters:
            self.add_row(parameter)
        if not self.rows:
            self.add_row()
        self.relayout()

    def parameters(self):
        """Return the completed rows as type/name/value dicts."""
        completed = []
        for entry in self.rows:
            name = entry['name'].text().strip()
            ptype = entry['type'].currentText()
            if name and ptype != PARAMETER_NONE:
                completed.append({'type': ptype, 'name': name, 'value': entry['value'].text()})
        return completed

    def relayout(self):
        for row, entry in enumerate(self.rows, start=1):
            for column, key in enumerate(('remove', 'type', 'name', 'value')):
                self.grid.addWidget(entry[key], row, column)

        # Park the extra height of the scroll viewport below the rows.
        for row in range(1, len(self.rows) + 1):
            self.grid.setRowStretch(row, 0)
        self.grid.setRowStretch(len(self.rows) + 1, 1)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.add_row()['type'].setFocus()
                return True
            if (event.key() == Qt.Key.Key_Tab
                    and event.modifiers() == Qt.KeyboardModifier.NoModifier
                    and self.rows
                    and watched is self.rows[-1]['value']):
                self.add_row()['type'].setFocus()
                return True
        return super().eventFilter(watched, event)


# ######################### Widgets
class Mupen64PlusForm(QMainWindow):

    def __init__(self):
        super().__init__()

        self.config = load_config()
        self.profile = Profile()
        self.current_rom = None
        self.controller_rows = []

        self.setWindowTitle('Mupen64Plus - GUI')

        content = QWidget()
        layout = QVBoxLayout(content)

        # Build the Games tab first: the folder rows refresh the ROM combos it owns.
        tabs = QTabWidget()
        tabs.addTab(self.build_tab(
            self.build_game_group(),
            self.build_controllers_group(),
            self.build_emulation_tabs(),
        ), 'Games')
        tabs.addTab(self.build_tab(self.build_folders_group()), 'Settings')
        tabs.addTab(self.build_tab(self.build_help_group()), 'Help')
        layout.addWidget(tabs)

        self.execute_button = QPushButton('Execute')
        self.execute_button.clicked.connect(self.execute)
        layout.addWidget(self.execute_button)

        self.setCentralWidget(content)

        self.rom_combo.currentIndexChanged.connect(self.apply_rom_parameters)
        self.apply_rom_parameters()

        self.resize(560, 660)

    @staticmethod
    def build_tab(*groups):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        for group in groups:
            layout.addWidget(group)
        layout.addStretch()
        return tab

    # ######################### Settings tab: folders (no config defaults)
    def build_folders_group(self):
        group = QGroupBox('Folders')

        form = QFormLayout(group)
        form.addRow('Mupen64Plus binaries folder', self.build_folder_row('mupen64plus_home'))
        form.addRow('N64 ROMs folder', self.build_folder_row('n64_roms_home'))
        form.addRow('GB/GBC ROMs folder', self.build_folder_row('gb_gbc_roms_home'))
        form.addRow('GB/GBC saves folder', self.build_folder_row('gb_gbc_saves_home'))
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
        for row in self.controller_rows:
            self.fill_rom_combo(row['gb'], self.config['gb_gbc_roms_home'], '*.gb*',
                                '(no GB/GBC ROMs folder set)')
        self.apply_rom_parameters()
        # Refilling combos cleared their selection; restore the current ROM's options.
        self.apply_rom_options(self.current_rom)

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

    @staticmethod
    def clear_combo(combo):
        """Deselect the current item, keeping a disabled placeholder visible."""
        if combo.isEnabled():
            combo.setCurrentIndex(-1)

    def apply_rom_parameters(self):
        """Save the previous ROM's parameters, then load the selected ROM's own."""
        rom = self.rom_combo.currentData()
        if rom == self.current_rom:
            return
        self.save_rom_parameters()
        self.current_rom = rom
        self.parameter_table.set_parameters(self.profile.for_rom(rom))
        self.apply_rom_options(rom)

    def apply_rom_options(self, rom):
        """Reset every field to its default, then apply the ROM's options."""
        options = self.profile.options_for_rom(rom)
        controllers = self.config['controllers']
        self.select_combo(self.video_combo, self.config['graphics']['video_plugin_default'])
        self.select_combo(self.emulation_mode_combo, self.config['emulation']['mode_default'])
        for row in self.controller_rows:
            self.select_combo(row['expansion'], controllers['expansion_pak_default'])
            self.select_combo(row['joystick'], controllers['joysticks']['default'])
            self.clear_combo(row['gb'])

        self.select_combo(self.video_combo, options.get('video_plugin') or '')
        self.select_combo(self.emulation_mode_combo, options.get('emulation_mode') or '')
        for row in self.controller_rows:
            self.select_combo(row['expansion'], options.get('expansion_pak') or '')
            self.select_combo(row['joystick'], options.get('joystick') or '')
            self.select_combo(row['gb'], options.get('gb_gbc_rom') or '')

    def save_rom_parameters(self):
        if self.current_rom:
            self.profile.set_rom(self.current_rom, self.parameter_table.parameters())

    def closeEvent(self, event):
        self.save_rom_parameters()
        super().closeEvent(event)

    def build_command(self):
        """Collect the Games-tab widgets into a :class:`Mupen64Plus` command."""
        mupen = Mupen64Plus(self.config)
        mupen.rom = self.rom_combo.currentData() or ''
        mupen.video_plugin = self.video_combo.currentText()
        mupen.resolution = self.resolution_edit.text().strip()
        mupen.emulation_mode = self.emulation_mode_combo.currentData() or ''
        mupen.parameters = self.parameter_table.parameters()
        mupen.controllers = [
            {
                'expansion_pak': row['expansion'].currentData(),
                'joystick': row['joystick'].currentText(),
                'gb_rom': row['gb'].currentData() or '',
            }
            for row in self.controller_rows
        ]
        return mupen

    def execute(self):
        self.save_rom_parameters()
        mupen = self.build_command()
        if not mupen.rom:
            QMessageBox.warning(self, 'Execute', 'No ROM file selected')
            return
        try:
            subprocess.Popen(mupen.command(), cwd=mupen.working_dir())
        except OSError as error:
            QMessageBox.warning(self, 'Execute', str(error))

    # ######################### N64 game + controllers
    def build_game_group(self):
        group = QGroupBox('N64 game')

        form = QFormLayout(group)

        self.rom_combo = QComboBox()
        self.fill_rom_combo(self.rom_combo, self.config['n64_roms_home'], '*.?64',
                            '(no N64 ROMs folder set)')
        form.addRow('N64 game', self.rom_combo)

        return group

    # ######################### controller loop
    def build_controllers_group(self):
        group = QGroupBox('Controllers')

        layout = QVBoxLayout(group)

        self.controller_tabs = QTabWidget()
        layout.addWidget(self.controller_tabs)

        row = QHBoxLayout()
        layout.addLayout(row)

        self.add_controller_button = QPushButton('Add controller')
        self.add_controller_button.clicked.connect(self.add_controller)
        row.addWidget(self.add_controller_button)

        self.remove_controller_button = QPushButton('Remove controller')
        self.remove_controller_button.clicked.connect(self.remove_controller)
        row.addWidget(self.remove_controller_button)

        self.add_controller()

        return group

    def add_controller(self):
        index = self.controller_tabs.count()
        if index >= len(self.config['controllers']['names']):
            return

        self.controller_tabs.addTab(
            self.build_controller_tab(),
            'Controller-{}'.format(index + 1))
        self.controller_tabs.setCurrentIndex(index)
        self.update_controller_buttons()

    def remove_controller(self):
        index = self.controller_tabs.count() - 1
        if index < 1:  # the first controller always stays
            return

        # Drop the last row so refresh_rom_combos stops walking it.
        self.controller_rows.pop()
        self.controller_tabs.widget(index).deleteLater()
        self.controller_tabs.removeTab(index)
        self.update_controller_buttons()

    def update_controller_buttons(self):
        count = self.controller_tabs.count()
        self.add_controller_button.setEnabled(count < len(self.config['controllers']['names']))
        self.remove_controller_button.setEnabled(count > 1)

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
        self.fill_rom_combo(gb_combo, self.config['gb_gbc_roms_home'], '*.gb*',
                            '(no GB/GBC ROMs folder set)')
        form.addRow('GB/GBC game', gb_combo)

        hint = QLabel('GB/GBC game is only used with the Transfer pak.')
        hint.setEnabled(False)
        form.addRow(hint)

        self.controller_rows.append({
            'expansion': expansion_combo,
            'joystick': joystick_combo,
            'gb': gb_combo,
        })

        return tab

    # ######################### Display and emulation / Core and plugin parameters
    def build_emulation_tabs(self):
        tabs = QTabWidget()
        # addTab makes the first added tab (Display and emulation) current.
        tabs.addTab(self.build_display_page(), 'Display and emulation')
        tabs.addTab(self.build_parameters_page(), 'Core/Plugin parameters')
        return tabs

    def build_parameters_page(self):
        page = QWidget()

        layout = QVBoxLayout(page)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.parameter_table = ParameterTable(self.config['parameters']['types'])
        scroll.setWidget(self.parameter_table)
        # Keep the page a constant size; extra rows scroll instead of growing the window.
        scroll.setFixedHeight(90)
        layout.addWidget(scroll)

        return page

    @staticmethod
    def build_help_group():
        group = QGroupBox('Core/Plugin parameters')
        layout = QVBoxLayout(group)

        for label, url in (('Core parameters ref.', CORE_PARAMETERS_URL),
                           ('Plugin parameters ref.', PLUGIN_PARAMETERS_URL)):
            button = QPushButton(label)
            button.clicked.connect(lambda _=False, url=url: QDesktopServices.openUrl(QUrl(url)))
            layout.addWidget(button)

        return group

    def build_display_page(self):
        page = QWidget()

        form = QFormLayout(page)

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

        return page


def main():
    app = QApplication(argv)

    window = Mupen64PlusForm()
    window.show()

    exit(app.exec())


if __name__ == '__main__':
    main()
