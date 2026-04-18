VERSION = "v.1.1.1"
################################
#  const.py
################################

import os


# This file contains constants used throughout the codebase.

# GENERAL THEMES
THEME_DARK = (35, 37, 42)
THEME_DARK2 = (53, 56, 64)
THEME_DARK3 = (66, 69, 79)
THEME_DARK4 = (90, 97, 115)

# COLORS
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

DEFAULT_SETTINGS = {
    "display_mode": "windowed",
    "program_monitor": "None",
    "lyrics_monitor": "None",
    "enable_lyrics": False,
    "lyrics_position": "Down",
    "background_color": "Green"
}

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SETTINGS_DIR = BASE_DIR / "savecloud"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
