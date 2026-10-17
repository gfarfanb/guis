#!/usr/bin/env python3
"""Build the Mupen64Plus UI Console command line from the Games-tab options.

Mirrors the final launch in the archived ``start-mupen64plus.bat`` wrapper. The
class holds the selected values as plain data so the command can be built and
tested without a GUI; ``Mupen64PlusForm`` fills it from the widgets.
"""

import os
import subprocess
from pathlib import Path

EXECUTABLE = 'mupen64plus-ui-console.exe' if os.name == 'nt' else 'mupen64plus-ui-console'

TRANSFER_PAK_ID = '4'


def mode_id(emulation):
    """Return the id of the default emulation mode label."""
    for mode in emulation['modes']:
        if mode['label'] == emulation['mode_default']:
            return mode['id']
    return emulation['modes'][0]['id'] if emulation['modes'] else '2'


class Mupen64Plus:
    """Assemble the ``mupen64plus-ui-console`` arguments for one game."""

    def __init__(self, config):
        self.config = config
        self.rom = ''                # full path to the selected N64 ROM
        self.video_plugin = ''
        self.resolution = ''
        self.emulation_mode = ''
        self.parameters = []         # Core/plugin type/name/value dicts
        self.extra = []              # extra leading options (batch's %*)
        self.controllers = []        # expansion_pak id, joystick, gb_rom per controller

    def command(self):
        """Return the argv list (``executable`` first, ROM last)."""
        config = self.config
        graphics = config['graphics']
        names = config['controllers']['names']

        argv = [self.executable(), *self.extra]

        argv += ['--set', 'Core[SaveSRAMPath]={}'.format(config['n64_saves_home'])]
        argv += ['--gfx', self.video_plugin or graphics['video_plugin_default']]
        argv += ['--resolution', self.resolution or graphics['resolution']]
        argv += ['--emumode', self.emulation_mode or mode_id(config['emulation'])]
        argv += ['--sshotdir', config['n64_screenshots_home']]

        for parameter in self.parameters:
            argv += ['--set', '{}[{}]={}'.format(
                parameter['type'], parameter['name'], parameter.get('value', ''))]

        for index, controller in enumerate(self.controllers):
            name = names[index]
            argv += ['--set', '{}[mode]=1'.format(name)]
            argv += ['--set', '{}[plugged]=True'.format(name)]
            argv += ['--set', '{}[name]={}'.format(name, controller['joystick'])]
            argv += ['--set', '{}[plugin]={}'.format(name, controller['expansion_pak'])]

            if str(controller['expansion_pak']) != TRANSFER_PAK_ID or not controller['gb_rom']:
                continue
            controller_id = index + 1
            argv += ['--gb-rom-{}'.format(controller_id), controller['gb_rom']]
            saves_home = config.get('gb_gbc_saves_home')
            if saves_home:
                argv += ['--gb-ram-{}'.format(controller_id),
                         str(Path(saves_home) / (Path(controller['gb_rom']).stem + '.sav'))]

        if self.rom:
            argv.append(self.rom)
        return argv

    def command_line(self):
        """Return the command as one quoted string (for display)."""
        return subprocess.list2cmdline(self.command())

    def executable(self):
        home = self.config.get('mupen64plus_home')
        return str(Path(home) / EXECUTABLE) if home else EXECUTABLE

    def working_dir(self):
        """Return the folder to run from, or ``None`` to inherit the cwd."""
        return self.config.get('mupen64plus_home') or None


if __name__ == '__main__':
    # Self-check: the batch wrapper's final command is reproduced option by option.
    import copy
    from config import DEFAULTS

    config = copy.deepcopy(DEFAULTS)
    config.update({
        'mupen64plus_home': 'C:/mupen',
        'n64_saves_home': 'C:/saves',
        'n64_screenshots_home': 'C:/shots',
        'gb_gbc_saves_home': 'C:/gb/saves',
    })

    mupen = Mupen64Plus(config)
    mupen.rom = 'C:/roms/Super Mario 64.z64'
    mupen.video_plugin = 'mupen64plus-video-rice'
    mupen.resolution = '800x600'
    mupen.emulation_mode = '2'
    mupen.parameters = [{'type': 'Core', 'name': 'OnScreenDisplay', 'value': 'true'}]
    mupen.controllers = [
        {'expansion_pak': '5', 'joystick': 'Keyboard', 'gb_rom': ''},
        {'expansion_pak': '4', 'joystick': 'Keyboard', 'gb_rom': 'C:/gb/Pokemon Blue Version.gb'},
    ]

    argv = mupen.command()
    assert argv[0].endswith(EXECUTABLE)
    assert 'Core[SaveSRAMPath]=C:/saves' in argv
    assert 'Core[OnScreenDisplay]=true' in argv
    assert argv[argv.index('--gfx') + 1] == 'mupen64plus-video-rice'
    assert argv[argv.index('--resolution') + 1] == '800x600'
    assert argv[argv.index('--emumode') + 1] == '2'
    assert argv[argv.index('--sshotdir') + 1] == 'C:/shots'
    assert 'Input-SDL-Control1[plugin]=5' in argv
    assert 'Input-SDL-Control2[plugin]=4' in argv
    assert '--gb-rom-2' in argv and argv[argv.index('--gb-rom-2') + 1] == 'C:/gb/Pokemon Blue Version.gb'
    assert argv[argv.index('--gb-ram-2') + 1] == str(Path('C:/gb/saves') / 'Pokemon Blue Version.sav')
    assert argv[-1] == 'C:/roms/Super Mario 64.z64'
    assert mupen.working_dir() == 'C:/mupen'
    assert 'Core[OnScreenDisplay]=true' in mupen.command_line()
    print('mupen command builds correctly')
