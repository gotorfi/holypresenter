import sys
from pathlib import Path

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