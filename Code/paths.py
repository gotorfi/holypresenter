import sys
from pathlib import Path

try:
    from PyQt6.QtGui import QIcon, QPixmap
except ImportError:
    from PySide6.QtGui import QIcon, QPixmap


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


# --------------------------------------------------
# CORE PATH LOGIC (FIXED CROSS-PLATFORM)
# --------------------------------------------------

def get_resource_base():
    """
    Returns correct root for assets in:
    - dev mode
    - PyInstaller (Windows/Linux/macOS)
    - macOS .app bundle
    """
    # PyInstaller
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)

    # macOS .app bundle safety
    if sys.platform == "darwin":
        # Code/ → project root is 2 levels up from file
        return PROJECT_ROOT

    # dev mode
    return PROJECT_ROOT


def get_app_path():
    """
    Where user data should go (NOT assets)
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    # macOS dev + Windows dev
    return PROJECT_ROOT


# --------------------------------------------------
# RESOURCE LOADER (CLEAN + NO GUESSING)
# --------------------------------------------------

def resource_path(rel):
    """
    Universal asset loader:
    works in dev + PyInstaller + macOS .app
    """
    base = get_resource_base()
    rel_path = Path(rel)

    if rel_path.is_absolute():
        return str(rel_path)

    # FORCE consistent asset structure
    # (NO fallback guessing anymore)
    return str(base / rel)


# --------------------------------------------------
# DATA PATH (UNCHANGED BUT SAFE)
# --------------------------------------------------

def data_path(rel):
    return str(get_app_path() / "savecloud" / rel)


# --------------------------------------------------
# ICON LOADER (SIMPLIFIED + ROBUST)
# --------------------------------------------------

def load_icon(icon_name):
    """
    Loads icon from disk reliably across:
    - PyQt6 / PySide6
    - macOS .app
    - PyInstaller EXE
    """

    icon = QIcon()

    # Qt resource system support (optional)
    if icon_name.startswith(":/"):
        pix = QPixmap(icon_name)
        if not pix.isNull():
            icon.addPixmap(pix)
            return icon

        icon_file = icon_name[2:].split("/")[-1]
        disk_path = resource_path(f"asset/ui/{icon_file}")

        if Path(disk_path).exists():
            return QIcon(disk_path)

        return QIcon()

    # normal file-based icons
    disk_path = resource_path(icon_name)

    if Path(disk_path).exists():
        return QIcon(disk_path)

    return QIcon()