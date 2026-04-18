import sys
import os
import shutil
import zipfile
import requests
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6 import uic
from PyQt6.QtCore import QTimer

import assets_rc
from paths import data_path, resource_path


# =========================
# CONFIG
# =========================
GITHUB_BASE = "https://github.com/gotorfi/holypresenter/releases/latest/download/"
FILES = {
    "core_windows": "holy-windows.zip",
    "core_mac": "holy-mac.zip",
}


# =========================
# WORKER
# =========================
class UpdateWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def find_app_root(self):
        # 1️⃣ install_path.txt
        try:
            f = Path(data_path("install_path.txt"))
            if f.exists():
                p = Path(f.read_text().strip())
                if p.exists():
                    return p
        except:
            pass

        # 2️⃣ fallback savecloud parent
        try:
            p = Path(data_path("")).parent / "HolyPresenter"
            if p.exists():
                return p
        except:
            pass

        # 3️⃣ search
        for root in [Path.home(), Path.cwd()]:
            try:
                for p in root.rglob("*"):
                    if sys.platform == "win32" and p.name == "HolyPresenter.exe":
                        return p.parent
                    if sys.platform == "darwin" and p.suffix == ".app":
                        return p
            except:
                continue

        return None

    def run(self):
        self.status.emit("Locating installation...")
        self.progress.emit(5)

        app_root = self.find_app_root()

        if not app_root:
            self.status.emit("HolyPresenter not found")
            self.progress.emit(100)
            self.finished.emit()
            return
        savecloud = Path(data_path(""))

        # -------------------------
        # TEMP FOLDER
        # -------------------------
        temp = Path(data_path("update_temp"))
        shutil.rmtree(temp, ignore_errors=True)
        temp.mkdir(parents=True, exist_ok=True)

        # -------------------------
        # DOWNLOAD
        # -------------------------
        self.status.emit("Downloading update...")

        file = FILES["core_mac"] if sys.platform == "darwin" else FILES["core_windows"]
        url = GITHUB_BASE + file
        zip_path = temp / file

        r = requests.get(url, stream=True)
        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total > 0:
                        percent = int((downloaded / total) * 40)
                        self.progress.emit(percent)

        # -------------------------
        # EXTRACT
        # -------------------------
        self.status.emit("Extracting...")

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(temp)

        self.progress.emit(50)

        # -------------------------
        # FIND NEW CONTENT
        # -------------------------
        new_root = None

        for exe in temp.rglob("HolyPresenter.exe"):
            new_root = exe.parent
            break

        if new_root is None:
            for app in temp.rglob("*.app"):
                new_root = app
                break

        if not new_root:
            self.status.emit("Update failed (no app)")
            self.finished.emit()
            return

        # -------------------------
        # DELETE OLD CONTENT (NOT FOLDER)
        # -------------------------
        self.status.emit("Cleaning old version...")

        for item in app_root.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
            except:
                pass

        self.progress.emit(70)

        # -------------------------
        # COPY NEW CONTENT
        # -------------------------
        self.status.emit("Installing update...")

        for item in new_root.iterdir():
            dest = app_root / item.name

            try:
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            except:
                pass

        self.progress.emit(90)

        # -------------------------
        # UPDATE SAVECLOUD (ADD ONLY)
        # -------------------------
        self.status.emit("Updating data...")

        new_savecloud = temp / "savecloud"

        if new_savecloud.exists():
            for item in new_savecloud.iterdir():
                dest = savecloud / item.name

                if not dest.exists():
                    try:
                        if item.is_dir():
                            shutil.copytree(item, dest)
                        else:
                            shutil.copy2(item, dest)
                    except:
                        pass

        self.progress.emit(100)

        # cleanup
        shutil.rmtree(temp, ignore_errors=True)

        self.finished.emit()


# =========================
# UI
# =========================
class Updater(QMainWindow):
    def __init__(self):
        super().__init__()

        self.page = uic.loadUi(resource_path("asset/installer4.ui"))

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.stack.addWidget(self.page)

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setFixedSize(900, 400)

        QTimer.singleShot(100, self.start_update)

    def start_update(self):
        self.page.Bar.setFixedWidth(0)

        self.worker = UpdateWorker()
        self.worker.progress.connect(self.update_bar)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.finish)

        self.worker.start()

    def update_bar(self, percent):
        width = int(882 * (percent / 100))
        self.page.Bar.setFixedWidth(width)

    def update_status(self, text):
        if hasattr(self.page, "status"):
            self.page.status.setText(text)

    def finish(self):
        QMessageBox.information(self, "Done", "Update completed!")
        self.close()


# =========================
# RUN
# =========================
def main():
    app = QApplication(sys.argv)
    win = Updater()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()