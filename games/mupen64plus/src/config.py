#!/usr/bin/env python3
"""Application configuration, stored in ``config.toml`` next to the app.

All settings live in one TOML file that is generated on first run.
``n64_roms_home`` and ``gb_gbc_roms_home`` have no default and are filled in by
the user.
"""

import copy
import json
import sys
import tomllib
from pathlib import Path

if getattr(sys, 'frozen', False):
    CONFIG_DIR = Path(sys.executable).resolve().parent
else:
    CONFIG_DIR = Path(__file__).resolve().parent

CONFIG_PATH = CONFIG_DIR / 'config.toml'

HEADER = [
    '# Mupen64Plus GUI configuration - generated automatically.',
    '# n64_roms_home and gb_gbc_roms_home have no default; set your folders.',
]

DEFAULTS = {
    # No defaults: the user must set these folders.
    'n64_roms_home': '',
    'gb_gbc_roms_home': '',
    'controllers': {
        'names': [
            'Input-SDL-Control1',
            'Input-SDL-Control2',
            'Input-SDL-Control3',
            'Input-SDL-Control4',
        ],
        'default': 1,
        'expansion_paks': [
            {'id': '1', 'label': 'None'},
            {'id': '2', 'label': 'Mem pak'},
            {'id': '4', 'label': 'Transfer pak'},
            {'id': '5', 'label': 'Rumble pak'},
        ],
        'expansion_pak_default': 'Rumble pak',
        'joysticks': {
            'names': ['Keyboard'],
            'default': 'Keyboard',
        },
    },
    'graphics': {
        'video_plugins': [
            'mupen64plus-video-glide64mk2',
            'mupen64plus-video-rice',
        ],
        'video_plugin_default': 'mupen64plus-video-glide64mk2',
        'resolution': '1024x768',
    },
    'emulation': {
        'modes': [
            {'id': '0', 'label': 'Pure Interpreter'},
            {'id': '1', 'label': 'Cached Interpreter'},
            {'id': '2', 'label': 'Dynamic Recompiler'},
        ],
        'mode_default': 'Dynamic Recompiler',
    },
}


def load_config():
    """Return the configuration, generating ``config.toml`` on first run."""
    if not CONFIG_PATH.exists():
        save_config(DEFAULTS)
        return copy.deepcopy(DEFAULTS)

    with open(CONFIG_PATH, 'rb') as handle:
        stored = tomllib.load(handle)

    return _merge(DEFAULTS, stored)


def save_config(config):
    """Write ``config`` to ``config.toml`` as a proper TOML document."""
    lines = list(HEADER)
    lines.append('')
    _write_table([], config, lines)
    CONFIG_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')


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
        lines.append('{} = {}'.format(key, _to_toml(value)))

    for key, value in tables.items():
        lines.append('')
        lines.append('[{}]'.format('.'.join(path + [key])))
        _write_table(path + [key], value, lines)

    for key, value in arrays.items():
        for item in value:
            lines.append('')
            lines.append('[[{}]]'.format('.'.join(path + [key])))
            _write_table(path + [key], item, lines)


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
