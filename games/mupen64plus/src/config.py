#!/usr/bin/env python3
"""Application configuration, stored in ``config.toml`` next to the app.

All settings live in one TOML file that is generated on first run.
``n64_roms_home`` and ``gb_gbc_roms_home`` have no default and are filled in by
the user.
"""

import copy
import json
import re
import sys
import tomllib
from pathlib import Path

if getattr(sys, 'frozen', False):
    CONFIG_DIR = Path(sys.executable).resolve().parent
    # PyInstaller extracts bundled data files under sys._MEIPASS.
    DATA_DIR = Path(getattr(sys, '_MEIPASS', CONFIG_DIR))
else:
    CONFIG_DIR = Path(__file__).resolve().parent
    DATA_DIR = CONFIG_DIR

CONFIG_PATH = CONFIG_DIR / 'config.toml'
DEFAULT_CONFIG_PATH = DATA_DIR / 'default_config.toml'

HEADER = [
    '# Mupen64Plus GUI configuration - generated automatically.',
    '# The *_home folders have no default; set them in the GUI.',
]


def load_defaults(path):
    """Return the committed defaults document at ``path``."""
    with open(path, 'rb') as handle:
        return tomllib.load(handle)


# Committed defaults, maintained in default_config.toml.
DEFAULTS = load_defaults(DEFAULT_CONFIG_PATH)


def load_config():
    """Return the configuration, generating ``config.toml`` on first run."""
    return load_toml(CONFIG_PATH, DEFAULTS)


def save_config(config):
    """Write ``config`` to ``config.toml`` as a proper TOML document."""
    save_toml(CONFIG_PATH, config)


def load_toml(path, defaults, header=HEADER):
    """Return ``defaults`` merged with the TOML at ``path``, creating it if missing."""
    path = Path(path)
    if not path.exists():
        save_toml(path, defaults, header)
        return copy.deepcopy(defaults)

    with open(path, 'rb') as handle:
        stored = tomllib.load(handle)

    return _merge(defaults, stored)


def save_toml(path, config, header=HEADER):
    """Write ``config`` to ``path`` as a proper TOML document."""
    lines = list(header)
    lines.append('')
    _write_table([], config, lines)
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _merge(defaults, stored):
    """Overlay ``stored`` on ``defaults``, recursing into nested tables."""
    merged = {}
    for key, default in defaults.items():
        if key not in stored:
            merged[key] = copy.deepcopy(default)
        elif isinstance(default, dict):
            merged[key] = _merge(default, stored[key])
        else:
            merged[key] = stored[key]

    for key, value in stored.items():
        if key not in merged:
            merged[key] = value

    return merged


def _is_table(value):
    return isinstance(value, dict)


def _is_table_array(value):
    return isinstance(value, list) and value and all(isinstance(item, dict) for item in value)


def _write_table(path, mapping, lines):
    """Append ``mapping`` to ``lines``, using ``path`` for nested headers."""
    scalars = {k: v for k, v in mapping.items() if not _is_table(v) and not _is_table_array(v)}
    tables = {k: v for k, v in mapping.items() if _is_table(v)}
    arrays = {k: v for k, v in mapping.items() if _is_table_array(v)}

    # Plain keys must come before any [table] header at this level.
    for key, value in scalars.items():
        lines.append('{} = {}'.format(_key(key), _to_toml(value)))

    for key, value in tables.items():
        lines.append('')
        lines.append('[{}]'.format('.'.join(_key(step) for step in path + [key])))
        _write_table(path + [key], value, lines)

    for key, value in arrays.items():
        for item in value:
            lines.append('')
            lines.append('[[{}]]'.format('.'.join(_key(step) for step in path + [key])))
            _write_table(path + [key], item, lines)


def _key(key):
    """Quote a key unless it is a valid bare TOML key."""
    return key if re.fullmatch(r'[A-Za-z0-9_-]+', key) else json.dumps(key)


def _to_toml(value):
    """Serialize simple values (str/int/bool/list) to an inline TOML value."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return '[' + ', '.join(_to_toml(item) for item in value) + ']'
    raise TypeError('unsupported config value: {!r}'.format(value))


if __name__ == '__main__':
    # Self-check: the emitted document must parse back to the same config.
    lines = []
    _write_table([], DEFAULTS, lines)
    assert tomllib.loads('\n'.join(lines)) == DEFAULTS
    print('config.toml round-trips correctly')
