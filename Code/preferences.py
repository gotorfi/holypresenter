from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QMainWindow,
    QPushButton,
    QCheckBox,
    QSplitter,
    QMessageBox
)

from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets, uic

import sys
from const import *
#from buttons import Buttons
import assets_rc

from messageservice import MessagingService

class PreferencesWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        uic.loadUi("Preferences.ui", self)
        self.setWindowIcon(QIcon(":/icon/icon.png"))
        self.main_window = main_window
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint
        )
        self.message_service = MessagingService()
    def set_enabled_recursive(self, widget, enabled=True):
        widget.setEnabled(enabled)
        for child in widget.findChildren(QWidget):
            child.setEnabled(enabled)
    def display_preferences_page(self, page=1):
        pages = [self.display_page, self.customize_page, self.system_page]

        for p in pages:
            p.hide()
            self.set_enabled_recursive(p, False)

        if page == 1:
            target = self.display_page
        elif page == 2:
            target = self.customize_page
        elif page == 3:
            target = self.system_page
            app_label = target.findChild(QLabel, "app_version")
            if app_label: app_label.setText(VERSION)
        else:
            return

        target.show()
        self.set_enabled_recursive(target, True)

        target.show()
        target.setEnabled(True)
    def manage_window(self, status="windowed"):
        if status == "windowed":
            self.main_window.showNormal()
        elif status == "fullscreen":
            self.main_window.showFullScreen()
        self.show()
        self.activateWindow()
        self.raise_()
    def RESTORE(self):
        if self.message_service.show_message("Restore Defaults", "Are you sure you want to restore default settings?\nThis cannot be undone.", options=2, icon=QMessageBox.Icon.Warning) == QMessageBox.StandardButton.Yes:
            self.hide()
            