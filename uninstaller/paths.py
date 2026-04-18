import sys
import os
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


# --------------------------------------------------
# RESOURCE ROOT
# --------------------------------------------------

def get_resource_base():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)

    if sys.platform == "darwin":
        return PROJECT_ROOT

    return PROJECT_ROOT


def resource_path(rel):
    base = get_resource_base()
    return str(base / rel)


# --------------------------------------------------
# USER DATA ROOT (FIXED)
# --------------------------------------------------

def get_app_data_root():
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "HolyPresenter"

    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "HolyPresenter"

    else:
        return Path.home() / ".local" / "share" / "HolyPresenter"


def data_path(rel=""):
    return str(get_app_data_root() / rel)


# --------------------------------------------------
# ICON LOADER
# --------------------------------------------------

def load_icon(icon_name):
    icon = QIcon()

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

    disk_path = resource_path(icon_name)

    if Path(disk_path).exists():
        return QIcon(disk_path)

    return QIcon()