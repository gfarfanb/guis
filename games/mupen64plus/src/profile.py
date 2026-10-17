#!/usr/bin/env python3
"""Per-ROM launch defaults, stored in ``profiles.toml`` next to ``config.toml``.

Replaces the legacy ``n64-profiles-win`` file sourced by
``start-mupen64plus.bat``: the same per-game options are keyed by ROM file name
(without extension) instead of the legacy SHA-256 hash, so a rename still
matches.
"""

import tomllib
from pathlib import Path

from config import CONFIG_DIR, load_toml

PROFILES_PATH = CONFIG_DIR / 'profiles.toml'

HEADER = [
    '# Mupen64Plus GUI ROM profiles - generated from the legacy n64-profiles-win.',
    '# One [games.<name>] table per ROM file name (without extension).',
    '# Empty values fall back to the matching config.toml default.',
]

DEFAULTS = {
    'games': {
        'Banjo-Kazooie': {
            'expansion_pak': 'Rumble pak',
            'joystick': 'Keyboard',
            'gb_gbc_rom': '',
            'video_plugin': 'mupen64plus-video-rice',
            'emulation_mode': 'Dynamic Recompiler',
        },
        'Banjo-Tooie': {
            'expansion_pak': 'Rumble pak',
            'joystick': 'Keyboard',
            'gb_gbc_rom': '',
            'video_plugin': 'mupen64plus-video-rice',
            'emulation_mode': 'Pure Interpreter',
        },
        'Pokemon Stadium': {
            'expansion_pak': 'Transfer pak',
            'joystick': 'Keyboard',
            'gb_gbc_rom': 'Pokemon Blue Version.gb',
            'video_plugin': 'mupen64plus-video-glide64mk2',
            'emulation_mode': 'Dynamic Recompiler',
        },
        'Pokemon Stadium 2': {
            'expansion_pak': 'Transfer pak',
            'joystick': 'Keyboard',
            'gb_gbc_rom': 'Pokemon Crystal Version.gbc',
            'video_plugin': 'mupen64plus-video-glide64mk2',
            'emulation_mode': 'Dynamic Recompiler',
        },
    },
}


class Profile:
    """Provide the stored launch defaults for a ROM file."""

    def __init__(self, path=PROFILES_PATH):
        self.path = Path(path)
        self.games = load_toml(self.path, DEFAULTS, HEADER)['games']

    def for_rom(self, rom_path):
        """Return the option table for ``rom_path``, or an empty dict."""
        return self.games.get(Path(rom_path).stem, {}) if rom_path else {}


if __name__ == '__main__':
    # Self-check: defaults resolve for the legacy ROM names and round-trip.
    profile = Profile()
    with open(profile.path, 'rb') as handle:
        assert tomllib.load(handle) == DEFAULTS
    assert profile.for_rom('C:/roms/Banjo-Kazooie.z64')['expansion_pak'] == 'Rumble pak'
    assert profile.for_rom('C:/roms/Pokemon Stadium.n64')['gb_gbc_rom'] == 'Pokemon Blue Version.gb'
    assert profile.for_rom('C:/roms/Unknown.n64') == {}
    assert profile.for_rom(None) == {}
    assert profile.games == DEFAULTS['games']
    print('profiles.toml round-trips correctly')
