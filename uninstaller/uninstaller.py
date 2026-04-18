import sys
import os
import shutil
import json
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6 import uic

import assets_rc

from paths import data_path, resource_path


# =========================
# WORKER
# =========================
class UninstallWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, option):
        super().__init__()
        self.option = option

    # -------------------------
    # FIND INSTALLATION (3-step system)
    # -------------------------
    def find_app_root(self):
        # 1️⃣ TRY: install_path.txt
        try:
            install_file = Path(data_path("install_path.txt"))
            if install_file.exists():
                saved_path = Path(install_file.read_text().strip())
                if saved_path.exists():
                    return saved_path
        except:
            pass

        # 2️⃣ TRY: common location (same folder as savecloud parent)
        try:
            possible = Path(data_path("")).parent / "HolyPresenter"
            if possible.exists():
                return possible
        except:
            pass

        # 3️⃣ FULL SEARCH (fallback)
        search_roots = []
        home = Path.home()

        if sys.platform == "win32":
            search_roots += [
                home / "Desktop",
                home / "Downloads",
                Path("C:/Program Files"),
                Path("C:/Program Files (x86)")
            ]
        else:
            search_roots += [
                Path("/Applications"),
                home / "Applications",
                home / "Desktop",
                home / "Downloads"
            ]

        search_roots.append(Path.cwd())

        for root in search_roots:
            if not root.exists():
                continue

            try:
                for path in root.rglob("*"):
                    if sys.platform == "win32" and path.name == "HolyPresenter.exe":
                        return path.parent

                    if sys.platform == "darwin" and path.suffix == ".app" and "HolyPresenter" in path.name:
                        return path

            except Exception:
                continue

        return None

    # -------------------------
    # MAIN RUN
    # -------------------------
    def run(self):
        app_path = self.find_app_root()
        savecloud = Path(data_path(""))

        if app_path is None:
            self.status.emit("HolyPresenter not found")
            self.finished.emit()
            return

        actions = self.option  # SET

        steps = []

        # =========================
        # CORE / ALL
        # =========================
        if "all" in actions or "core" in actions:
            steps.append(("Removing HolyPresenter", app_path))

        # =========================
        # SAVECLOUD
        # =========================
        if "all" in actions or "savecloud" in actions:
            steps.append(("Removing savecloud", savecloud))

        # =========================
        # SUB FOLDERS
        # =========================
        if "galleries" in actions:
            steps.append(("Removing galleries", savecloud / "galleries"))

        if "backgrounds" in actions:
            steps.append(("Removing backgrounds", savecloud / "backgrounds"))

        if "media" in actions:
            steps.append(("Removing media", savecloud / "media"))

        # =========================
        # SPECIAL: songs clear
        # =========================
        if "songs_clear" in actions:
            steps.append(("Clearing songs", savecloud / "galleries" / "playlists.json"))

        total = len(steps)

        if total == 0:
            self.status.emit("Nothing to remove")
            self.finished.emit()
            return

        for i, (name, path) in enumerate(steps):
            self.status.emit(name)

            try:
                if name == "Clearing songs":
                    if path.exists():
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        data["songs"] = []

                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)

                else:
                    if path.exists():
                        shutil.rmtree(path, ignore_errors=True)

            except Exception as e:
                self.status.emit(f"Error: {e}")

            percent = int(((i + 1) / total) * 100)
            self.progress.emit(percent)

        self.finished.emit()


# =========================
# UI
# =========================
class Uninstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self._updating = False

        self.page1 = uic.loadUi(resource_path("asset/uninstaller.ui"))
        self.page2 = uic.loadUi(resource_path("asset/uninstaller2.ui"))

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)

        self.page1.opt_1.stateChanged.connect(self.handle_checkbox_logic)
        self.page1.opt_2.stateChanged.connect(self.handle_checkbox_logic)
        self.page1.opt_3.stateChanged.connect(self.handle_checkbox_logic)
        self.page1.opt_4.stateChanged.connect(self.handle_checkbox_logic)
        self.page1.opt_5.stateChanged.connect(self.handle_checkbox_logic)
        self.page1.opt_6.stateChanged.connect(self.handle_checkbox_logic)

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setFixedSize(800, 700)

        self.init_ui()

    # -------------------------
    def init_ui(self):
        self.page1.uninstall.clicked.connect(self.confirm_uninstall)

        self.page2.close.setEnabled(False)
        self.page2.close.clicked.connect(self.close_app)

    # -------------------------


    def handle_checkbox_logic(self):
        if self._updating:
            return

        self._updating = True

        try:
            o1 = self.page1.opt_1
            o2 = self.page1.opt_2
            o3 = self.page1.opt_3
            o4 = self.page1.opt_4
            o5 = self.page1.opt_5
            o6 = self.page1.opt_6

            # =========================
            # OPT 1 = ALL
            # =========================
            if o1.isChecked():
                for o in [o2, o3, o4, o5, o6]:
                    o.blockSignals(True)
                    o.setChecked(True)
                    o.setEnabled(False)
                    o.blockSignals(False)
                return

            # reset enable
            for o in [o2, o3, o4, o5, o6]:
                o.blockSignals(True)
                o.setEnabled(True)
                o.blockSignals(False)

            # =========================
            # OPT 2 = SAVECLOUD + CORE
            # =========================
            if o2.isChecked():
                o1.blockSignals(True)
                o1.setChecked(False)
                o1.blockSignals(False)

                for o in [o3, o4, o5, o6]:
                    o.blockSignals(True)
                    o.setChecked(True)
                    o.setEnabled(False)
                    o.blockSignals(False)

            # =========================
            # OPT 3 overrides OPT 6
            # =========================
            if o3.isChecked():
                o6.blockSignals(True)
                o6.setChecked(False)
                o6.setEnabled(False)
                o6.blockSignals(False)

            # =========================
            # OPT 4 / OPT 5 safety
            # =========================
            if o4.isChecked() or o5.isChecked():
                o1.blockSignals(True)
                o1.setChecked(False)
                o1.blockSignals(False)

            # =========================
            # OPT 6 safety
            # =========================
            if o6.isChecked() and o3.isChecked():
                o6.blockSignals(True)
                o6.setChecked(False)
                o6.blockSignals(False)

        finally:
            self._updating = False


    def get_selected_actions(self):
        actions = set()

        if self.page1.opt_1.isChecked():
            return {"all"}  # hard override

        if self.page1.opt_2.isChecked():
            actions.add("savecloud")
            actions.add("core")

        if self.page1.opt_3.isChecked():
            actions.add("galleries")
            actions.add("core")

        if self.page1.opt_4.isChecked():
            actions.add("backgrounds")
            actions.add("core")

        if self.page1.opt_5.isChecked():
            actions.add("media")
            actions.add("core")

        if self.page1.opt_6.isChecked():
            actions.add("songs_clear")
            actions.add("core")

        return actions

    # -------------------------
    def confirm_uninstall(self):
        actions = self.get_selected_actions()

        if not actions:
            QMessageBox.warning(self, "Warning", "Select an option!")
            return

        reply = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to delete selected data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.start_uninstall(actions)

    # -------------------------
    def start_uninstall(self, option):
        self.stack.setCurrentWidget(self.page2)

        self.page2.bar.setValue(0)
        self.page2.removestatus.setText("")
        self.page2.status.setText("Removing...")
        self.page2.close.setEnabled(False)

        self.worker = UninstallWorker(option)
        self.worker.progress.connect(self.page2.bar.setValue)
        self.worker.status.connect(self.page2.removestatus.setText)
        self.worker.finished.connect(self.finish_uninstall)
        self.worker.start()

    # -------------------------
    def finish_uninstall(self):
        self.page2.removestatus.setText("")
        self.page2.status.setText("Uninstallation complete. You can close now.")
        self.page2.close.setEnabled(True)

    def close_app(self):
        # Deletion here later
        self.close()


# =========================
# RUN
# =========================
def main():
    app = QApplication(sys.argv)
    win = Uninstaller()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()