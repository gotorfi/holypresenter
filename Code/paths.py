import sys
from pathlib import Path

try:
    from PyQt6.QtGui import QIcon, QPixmap
except ImportError:
    from PySide6.QtGui import QIcon, QPixmap

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


def get_resource_base():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return PROJECT_ROOT


def get_app_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return PROJECT_ROOT


def resource_path(rel):
    rel_path = Path(rel)
    base = get_resource_base()

    if rel_path.is_absolute():
        return str(rel_path)

    if not rel.startswith("asset"):
        candidate = base / "asset" / rel
        if candidate.exists():
            return str(candidate)

    candidate = base / rel
    if candidate.exists():
        return str(candidate)

    return str(base / "asset" / rel) if not rel.startswith("asset") else str(candidate)


def data_path(rel):
    return str(get_app_path() / "savecloud" / rel)


def load_icon(icon_name):
    """
    Load an icon with fallback from disk when resource system fails.
    Works with old PyQt6 on macOS by loading from disk instead of resources.
    """
    icon = QIcon()
    
    if icon_name.startswith(":/"):
        icon.addPixmap(QPixmap(icon_name))
        if not icon.isNull():
            return icon
        
        icon_file = icon_name[2:].split("/")[-1]
        disk_path = resource_path(f"asset/ui/{icon_file}")
        if Path(disk_path).exists():
            return QIcon(disk_path)
    else:
        disk_path = resource_path(icon_name)
        if Path(disk_path).exists():
            return QIcon(disk_path)
    
    return QIcon()
