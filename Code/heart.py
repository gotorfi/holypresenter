from PyQt6.QtWidgets import (
    QApplication,
    QToolButton,
    QWidget,
    QLabel,
    QMainWindow,
    QPushButton,
    QCheckBox,
    QSplitter,
    QStackedWidget,
    QMenu
)

from PyQt6.QtGui import QAction, QIcon, QFont, QKeySequence, QPixmap
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets, uic

import sys
from const import *
from buttons import Buttons
import assets_rc


class heart(QMainWindow):
    def __init__(self):
        super().__init__()
    
        uic.loadUi("mainpage.ui", self)
        self.main_page = self.centralWidget()
        self.editor_page = uic.loadUi("editor.ui")
        self.setWindowIcon(QIcon("icon.png"))
        screen = QApplication.primaryScreen()
        size = screen.size()

        self.screenx = size.width()
        self.screeny = size.height()

        self.resize(self.screenx, self.screeny)
        self.showMaximized()
        self.stack = QStackedWidget()

        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.editor_page)

        self.setCentralWidget(self.stack)

        self.initUI()
        self.buttons = Buttons(self)

       


       
    def initUI(self):

        self.new_list = self.findChild(QToolButton, "new_list")
        New_menu = QMenu(self)

        action_playlist = QAction("New Playlist", self)
        action_playlist.setShortcut(QKeySequence("Ctrl+Alt+N"))

        action_slideshow = QAction("New Slideshow", self)
        action_slideshow.setShortcut(QKeySequence("Ctrl+Alt+S"))

        action_lyricshow = QAction("New Lyricsshow", self)
        action_lyricshow.setShortcut(QKeySequence("Ctrl+Alt+L"))

        New_menu.addAction(action_playlist)
        New_menu.addAction(action_slideshow)
        New_menu.addAction(action_lyricshow)

        self.new_list.setMenu(New_menu)
        self.new_list.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)



        self.menubar.setStyleSheet(f"""
        QMenuBar {{
            background-color: rgb{THEME_DARK};
            color: rgb{COLOR_WHITE};
        }}
        QMenuBar::item {{
            background-color: transparent;
            color: rgb{COLOR_WHITE};
        }}
        QMenu {{
                background-color: rgb{THEME_DARK};
                color: rgb{COLOR_WHITE};
                border: 1px solid gray;
            }}
        QMenuBar::item:selected {{
            background-color: rgb(80, 80, 80);
            color: rgb{COLOR_WHITE};
        }}
    """)
        self.actionClose_Editor.setEnabled(False)
        self.menuEdit.setStyleSheet("""
            QMenu::item:disabled {
                color: gray;
            }
            QMenu::item:enabled {
                color: white;
            }
            QMenu::item:selected {
                background-color: rgb(80, 80, 80);
                                    
            """)
        

def main():
    app = QApplication(sys.argv)
    window = heart()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()