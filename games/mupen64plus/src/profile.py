#!/usr/bin/env python3
"""Per-ROM launch options and Core/plugin parameters, in ``profiles.toml`` next to ``config.toml``.

One ``[[games.<name>]]`` entry per ROM file name (without extension); each entry
is a ``type``/``name``/``value`` parameter that loads into the GUI's
*Core/Plugin parameters* widget. Only the types declared in ``config.toml``
``[parameters].types`` are kept.

An ``[options.<name>]`` table holds the ROM's launch options (video plugin,
emulation mode, expansion pak, joystick, GB/GBC ROM); missing keys fall back to
``config.toml``.
"""

from pathlib import Path

from config import (
    CONFIG_DIR,
    DATA_DIR,
    load_config,
    load_defaults,
    load_toml,
    save_toml,
)

PROFILES_PATH = CONFIG_DIR / 'profiles.toml'
DEFAULT_PROFILES_PATH = DATA_DIR / 'default_profiles.toml'

HEADER = [
    '# Mupen64Plus GUI ROM profiles.',
    '# [options.<name>] launch options (empty/missing fall back to config.toml).',
    '# One [[games.<name>]] entry per ROM file name (without extension) per parameter.',
    '# Only Core/plugin parameter types (config.toml [parameters].types) are kept.',
    '#',
    '# Example (passes --set Core[OnScreenDisplay]=true):',
    '# [[games."Super Mario 64"]]',
    '# type = "Core"',
    '# name = "OnScreenDisplay"',
    '# value = "true"',
]

# Committed defaults, maintained in default_profiles.toml.
DEFAULTS = load_defaults(DEFAULT_PROFILES_PATH)


class Profile:
    """Store the launch options and Core/plugin parameters for each ROM file."""

    def __init__(self, path=PROFILES_PATH):
        self.path = Path(path)
        self.types = load_config()['parameters']['types']
        stored = load_toml(self.path, DEFAULTS, HEADER)
        # Drop anything that is not a parameter list (old profile schema).
        self.games = {
            name: entries
            for name, entries in stored['games'].items()
            if isinstance(entries, list)
        }
        self.options = {
            name: table
            for name, table in stored.get('options', {}).items()
            if isinstance(table, dict)
        }

    def for_rom(self, rom_path):
        """Return the valid parameter list for ``rom_path``."""
        if not rom_path:
            return []
        return [
            {'type': entry['type'], 'name': entry['name'], 'value': entry.get('value', '')}
            for entry in self.games.get(Path(rom_path).stem, [])
            if entry.get('type') in self.types and entry.get('name')
        ]

    def options_for_rom(self, rom_path):
        """Return the launch-option table for ``rom_path``, or an empty dict."""
        if not rom_path:
            return {}
        return self.options.get(Path(rom_path).stem, {})

    def set_rom(self, rom_path, parameters):
        """Store ``parameters`` (type/name/value dicts) for ``rom_path`` and save."""
        if not rom_path:
            return
        name = Path(rom_path).stem
        if parameters:
            self.games[name] = parameters
        else:
            self.games.pop(name, None)
        save_toml(self.path, {'options': self.options, 'games': self.games}, HEADER)


if __name__ == '__main__':
    # Self-check: parameters and launch options round-trip, rename by extension
    # still matches, and non-Core/plugin entries are dropped.
    import tempfile

    options = {'expansion_pak': 'Transfer pak', 'gb_gbc_rom': 'Pokemon Crystal Version.gbc'}
    path = Path(tempfile.mkdtemp()) / 'profiles.toml'
    save_toml(path, {'options': {'Test ROM': options}, 'games': {}}, HEADER)
    profile = Profile(path)
    assert profile.for_rom('C:/roms/Unknown.n64') == []
    assert profile.for_rom(None) == []
    assert profile.options_for_rom('C:/roms/Test ROM.z64') == options
    assert profile.options_for_rom('C:/roms/Unknown.n64') == {}
    assert profile.options_for_rom(None) == {}

    params = [{'type': 'Core', 'name': 'DisableExtraMem', 'value': 'True'}]
    profile.set_rom('C:/roms/Banjo-Kazooie.z64', params)
    assert Profile(path).for_rom('C:/roms/Banjo-Kazooie.n64') == params
    assert Profile(path).options_for_rom('C:/roms/Test ROM.n64') == options

    save_toml(path, {'games': {'Bad': [
        {'type': 'None', 'name': 'x', 'value': ''},
        {'type': 'Bogus', 'name': 'y', 'value': ''},
        {'type': 'Core', 'name': '', 'value': ''},
    ]}}, HEADER)
    assert Profile(path).for_rom('Bad') == []

    profile.set_rom('C:/roms/Banjo-Kazooie.z64', [])
    assert Profile(path).for_rom('C:/roms/Banjo-Kazooie.n64') == []
    print('profiles.toml round-trips correctly')
