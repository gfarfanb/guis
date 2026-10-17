#!/usr/bin/env python3
"""Application configuration, stored in ``config.toml`` next to the app.

All settings live in one TOML file that is generated on first run.
``n64_roms_home`` and ``gb_gbc_roms_home`` have no default and are filled in by
the user.
"""

import json
import sys
import tomllib
from pathlib import Path

if getattr(sys, 'frozen', False):
    CONFIG_DIR = Path(sys.executable).resolve().parent
else:
    CONFIG_DIR = Path(__file__).resolve().parent

CONFIG_PATH = CONFIG_DIR / 'config.toml'

DEFAULTS = {
    # No defaults: the user must set these folders.
    'n64_roms_home': '',
    'gb_gbc_roms_home': '',
    'controller_names': [
        'Input-SDL-Control1',
        'Input-SDL-Control2',
        'Input-SDL-Control3',
        'Input-SDL-Control4',
    ],
    'controllers_default': 1,
    'expansion_paks': [
        ['1', 'None'],
        ['2', 'Mem pak'],
        ['4', 'Transfer pak'],
        ['5', 'Rumble pak'],
    ],
    'expansion_pak_default': 'Rumble pak',
    'gfx_video_plugins': [
        'mupen64plus-video-glide64mk2',
        'mupen64plus-video-rice',
    ],
    'gfx_video_plugin_default': 'mupen64plus-video-glide64mk2',
    'resolution_default': '1024x768',
    'emulation_modes': [
        ['0', 'Pure Interpreter'],
        ['1', 'Cached Interpreter'],
        ['2', 'Dynamic Recompiler'],
    ],
    'emulation_mode_default': 'Dynamic Recompiler',
    'configured_joystick_names': ['Keyboard'],
    'configured_joystick_default': 'Keyboard',
}


def load_config():
    """Return the configuration, generating ``config.toml`` on first run."""
    if not CONFIG_PATH.exists():
        save_config(DEFAULTS)
        return dict(DEFAULTS)

    with open(CONFIG_PATH, 'rb') as handle:
        stored = tomllib.load(handle)

    return {**DEFAULTS, **stored}


def save_config(config):
    """Write ``config`` to ``config.toml``."""
    lines = [
        '# Mupen64Plus GUI configuration - generated automatically.',
        '# n64_roms_home and gb_gbc_roms_home have no default; set your folders.',
        '',
    ]
    for key, value in config.items():
        lines.append('{} = {}'.format(key, _to_toml(value)))

    CONFIG_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _to_toml(value):
    """Serialize the config's simple values (str/int/bool/list) to TOML."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return '[' + ', '.join(_to_toml(item) for item in value) + ']'
    raise TypeError('unsupported config value: {!r}'.format(value))
