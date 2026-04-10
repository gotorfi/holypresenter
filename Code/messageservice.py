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
from paths import resource_path, data_path

import sys
from const import *
try:
    if sys.platform == "darwin":
        import assets_rc_mac as assets_rc
    else:
        import assets_rc
except Exception:
    import assets_rc

class MessagingService:
    def __init__(self):
        pass
    def show_message(self, title, message, options=1, icon=QMessageBox.Icon.Warning):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.setWindowIcon(QIcon(resource_path("asset/ui/icon.png")))

        if options == 1:
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        elif options == 2:
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        else:
            return None

        return msg.exec()