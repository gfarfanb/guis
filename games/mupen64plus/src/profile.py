#!/usr/bin/env python3
"""Per-ROM Core/plugin parameters, stored in ``profiles.toml`` next to ``config.toml``.

One ``[[games.<name>]]`` entry per ROM file name (without extension); each entry
is a ``type``/``name``/``value`` parameter that loads into the GUI's
*Core/Plugin parameters* widget. Only the types declared in ``config.toml``
``[parameters].types`` are kept.
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
    """Store the Core/plugin parameters for each ROM file."""

    def __init__(self, path=PROFILES_PATH):
        self.path = Path(path)
        self.types = load_config()['parameters']['types']
        # Drop anything that is not a parameter list (old profile schema).
        self.games = {
            name: entries
            for name, entries in load_toml(self.path, DEFAULTS, HEADER)['games'].items()
            if isinstance(entries, list)
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

    def set_rom(self, rom_path, parameters):
        """Store ``parameters`` (type/name/value dicts) for ``rom_path`` and save."""
        if not rom_path:
            return
        name = Path(rom_path).stem
        if parameters:
            self.games[name] = parameters
        else:
            self.games.pop(name, None)
        save_toml(self.path, {'games': self.games}, HEADER)


if __name__ == '__main__':
    # Self-check: parameters round-trip, rename by extension still matches, and
    # non-Core/plugin entries are dropped.
    import tempfile

    path = Path(tempfile.mkdtemp()) / 'profiles.toml'
    profile = Profile(path)
    assert profile.for_rom('C:/roms/Unknown.n64') == []
    assert profile.for_rom(None) == []

    params = [{'type': 'Core', 'name': 'DisableExtraMem', 'value': 'True'}]
    profile.set_rom('C:/roms/Banjo-Kazooie.z64', params)
    assert Profile(path).for_rom('C:/roms/Banjo-Kazooie.n64') == params

    save_toml(path, {'games': {'Bad': [
        {'type': 'None', 'name': 'x', 'value': ''},
        {'type': 'Bogus', 'name': 'y', 'value': ''},
        {'type': 'Core', 'name': '', 'value': ''},
    ]}}, HEADER)
    assert Profile(path).for_rom('Bad') == []

    profile.set_rom('C:/roms/Banjo-Kazooie.z64', [])
    assert Profile(path).for_rom('C:/roms/Banjo-Kazooie.n64') == []
    print('profiles.toml round-trips correctly')
