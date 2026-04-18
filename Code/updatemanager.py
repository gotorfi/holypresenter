import sys
import requests
import subprocess
import os
import re
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6 import uic

from const import VERSION
from paths import resource_path, load_icon
from messageservice import MessagingService


# =========================
# URLS (RAW!)
# =========================
BASE = "https://raw.githubusercontent.com/gotorfi/holypresenter/main"

CONST_URL = f"{BASE}/Code/const.py"
UPDATE_TXT_URL = f"{BASE}/details/update.txt"
THUMB_URL = f"{BASE}/details/updatethumb.png"


class UpdateManager(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.msg = MessagingService()

        self.latest_version = None
        self.update_info = ""

        if not self.check_for_update():
            self.msg.show_message(
                "Up to date",
                f"You are using the latest version ({VERSION})",
                1
            )
            return

        # =========================
        # LOAD UI
        # =========================
        uic.loadUi(resource_path("asset/updatemanager.ui"), self)

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setFixedSize(self.size())

        self.setWindowIcon(load_icon("asset/ui/icon.png"))

        # =========================
        # SET DATA
        # =========================
        self.title.setText(f"Holy Presenter {self.latest_version}")
        self.info.setText(self.update_info)

        self.load_thumb()

        # =========================
        # BUTTONS
        # =========================
        self.cancel.clicked.connect(self.close)
        self.update.clicked.connect(self.confirm_update)

        self.show()

    # =========================
    # VERSION CHECK
    # =========================
    def check_for_update(self):
        try:
            r = requests.get(CONST_URL, timeout=5)
            text = r.text

            match = re.search(r'VERSION\s*=\s*"([^"]+)"', text)
            if not match:
                return False

            self.latest_version = match.group(1)

            if self.latest_version == VERSION:
                return False

            # LOAD UPDATE INFO
            r2 = requests.get(UPDATE_TXT_URL, timeout=5)
            self.update_info = r2.text

            return True

        except Exception as e:
            print("Update check failed:", e)
            return False

    # =========================
    # LOAD IMAGE
    # =========================
    def load_thumb(self):
        try:
            r = requests.get(THUMB_URL, timeout=5)

            temp_dir = Path(os.getenv("TEMP") or "/tmp")
            temp = temp_dir / "update_thumb.png"

            with open(temp, "wb") as f:
                f.write(r.content)

            pixmap = QPixmap(str(temp))
            self.thumb.setPixmap(pixmap)

        except Exception as e:
            print("Image load failed:", e)

    # =========================
    # CONFIRM UPDATE
    # =========================
    def confirm_update(self):
        result = self.msg.show_message(
            "Update",
            "Are you sure you want to update?\n\n"
            "You will NOT lose any data.\n"
            "Old version will be replaced.",
            options=2
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        self.start_update()

    # =========================
    # GET APP ROOT (robust)
    # =========================
    def get_app_root(self):
        # PyInstaller exe/app
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent

        # dev mode fallback
        return Path(__file__).resolve().parent.parent

    # =========================
    # START UPDATE
    # =========================
    def start_update(self):
        self.close()

        app = QApplication.instance()
        if app:
            for w in app.topLevelWidgets():
                try:
                    w.close()
                except:
                    pass

        app_root = self.get_app_root()

        try:
            if sys.platform == "win32":
                updater_exe = app_root / "Updater.exe"

                if updater_exe.exists():
                    subprocess.Popen([str(updater_exe)])
                else:
                    # DEV fallback
                    updater_py = app_root / "updater" / "updater.py"
                    if updater_py.exists():
                        subprocess.Popen([sys.executable, str(updater_py)])
                    else:
                        print("Updater not found (exe or py)")

            elif sys.platform == "darwin":
                updater_app = app_root / "Updater.app"

                if updater_app.exists():
                    subprocess.Popen(["open", "-n", str(updater_app)])
                else:
                    # DEV fallback
                    updater_py = app_root / "updater" / "updater.py"
                    if updater_py.exists():
                        subprocess.Popen([sys.executable, str(updater_py)])
                    else:
                        print("Updater not found (app or py)")

        except Exception as e:
            print("Failed to launch updater:", e)