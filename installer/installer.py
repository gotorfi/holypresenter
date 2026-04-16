import sys
import os
import requests
import zipfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QStackedWidget
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6 import uic

from paths import resource_path
import assets_rc


# =========================
# CONFIG
# =========================
GITHUB_BASE = "https://github.com/gotorfi/holypresenter/releases/latest/download/"

FILES = {
    "core_windows": "holy-windows.zip",
    "core_mac": "holy-mac.zip",
    "savecloud": "savecloud.zip",
    "backgrounds": "backgrounds.zip",
    "starter": "starterpack.zip",
    "lyrics": "lyricsshow.zip",
}


# =========================
# DOWNLOADER
# =========================
class MultiDownloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, files, install_path):
        super().__init__()
        self.files = files
        self.install_path = Path(install_path)

    def run(self):
        total_size = 0
        downloaded_total = 0

        sizes = {}

        for f in self.files:
            try:
                r = requests.head(GITHUB_BASE + f, allow_redirects=True)
                size = int(r.headers.get("content-length", 0))
            except:
                size = 0
            sizes[f] = size
            total_size += size

        for f in self.files:
            try:
                url = GITHUB_BASE + f
                dest = self.install_path / f

                r = requests.get(url, stream=True)
                r.raise_for_status()

                with open(dest, "wb") as file:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            file.write(chunk)
                            downloaded_total += len(chunk)

                            if total_size > 0:
                                percent = int(downloaded_total / total_size * 100)
                                self.progress.emit(percent)

            except Exception as e:
                print("Download error:", e)

        self.finished.emit()


# =========================
# INSTALLER
# =========================
class Installer(QMainWindow):
    def __init__(self):
        super().__init__()

        # LOAD UI PAGES
        self.page1 = uic.loadUi(resource_path("asset/installer.ui"))
        self.page2 = uic.loadUi(resource_path("asset/installer2.ui"))
        self.page3 = uic.loadUi(resource_path("asset/installer3.ui"))
        self.page4 = uic.loadUi(resource_path("asset/installer4.ui"))

        # STACK (IMPORTANT FIX)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)
        self.stack.addWidget(self.page3)
        self.stack.addWidget(self.page4)

        self.install_path = ""

        self.init_pages()
        self.set_sizes()

    # =========================
    # NAVIGATION
    # =========================
    def set_page(self, page):
        self.stack.setCurrentWidget(page)

    # =========================
    # INIT
    # =========================
    def init_pages(self):

        # PAGE 1
        self.page1.next.clicked.connect(lambda: self.set_page(self.page2))

        # PAGE 2
        self.page2.next.clicked.connect(self.validate_page2)
        self.page2.back.clicked.connect(lambda: self.set_page(self.page1))
        self.page2.explorer.clicked.connect(self.select_folder)

        # PAGE 3
        self.page3.back.clicked.connect(lambda: self.set_page(self.page2))
        self.page3.install.setEnabled(False)
        self.page3.LicenseBox.stateChanged.connect(self.toggle_install)
        self.page3.install.clicked.connect(self.start_install)

    # =========================
    # PAGE 2
    # =========================
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select install location")
        if folder:
            self.install_path = folder
            self.page2.location.setText(folder)

    def validate_page2(self):
        if not self.page2.location.text():
            QMessageBox.warning(self, "Warning", "Please select install location!")
            return
        self.set_page(self.page3)

    # =========================
    # PAGE 3
    # =========================
    def toggle_install(self):
        self.page3.install.setEnabled(self.page3.LicenseBox.isChecked())

    # =========================
    # PAGE 4
    # =========================
    def update_progress(self, percent):
        width = int(882 * (percent / 100))
        self.page4.Bar.setFixedWidth(width)

    # =========================
    # FILE SIZES
    # =========================
    def get_size_mb(self, filename):
        try:
            r = requests.head(GITHUB_BASE + filename, allow_redirects=True)
            size = int(r.headers.get("content-length", 0))
            return round(size / (1024 * 1024), 1)
        except:
            return 0

    def set_sizes(self):
        self.page2.option1.setText(f"Backgrounds pack ({self.get_size_mb(FILES['backgrounds'])} MB)")
        self.page2.option2.setText(f"Starter pack ({self.get_size_mb(FILES['starter'])} MB)")
        self.page2.option3.setText(f"LyricsShow pack ({self.get_size_mb(FILES['lyrics'])} MB)")

    # =========================
    # INSTALL
    # =========================
    def start_install(self):

        if not self.install_path:
            QMessageBox.warning(self, "Error", "No install location selected!")
            return

        Path(self.install_path).mkdir(parents=True, exist_ok=True)

        self.set_page(self.page4)

        files = []

        if sys.platform == "darwin":
            files.append(FILES["core_mac"])
        else:
            files.append(FILES["core_windows"])

        files.append(FILES["savecloud"])

        if self.page2.option1.isChecked():
            files.append(FILES["backgrounds"])

        if self.page2.option2.isChecked():
            files.append(FILES["starter"])

        if self.page2.option3.isChecked():
            files.append(FILES["lyrics"])

        self.downloader = MultiDownloader(files, self.install_path)
        self.downloader.progress.connect(self.update_progress)
        self.downloader.finished.connect(self.install_finished)
        self.downloader.start()

    # =========================
    # FINISH
    # =========================
    def extract_all(self):
        for file in Path(self.install_path).glob("*.zip"):
            try:
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    zip_ref.extractall(self.install_path)
                file.unlink()
            except Exception as e:
                print("Extract error:", e)

    def launch_app(self):
        if sys.platform == "darwin":
            os.system(f'open "{self.install_path}/HolyPresenter.app"')
        else:
            exe = Path(self.install_path) / "HolyPresenter" / "HolyPresenter.exe"
            if exe.exists():
                os.startfile(exe)

    def install_finished(self):
        self.extract_all()
        QMessageBox.information(self, "Done", "Installation finished!")
        self.launch_app()
        self.close()


# =========================
# RUN
# =========================
def main():
    app = QApplication(sys.argv)
    window = Installer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()