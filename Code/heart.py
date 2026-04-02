from PyQt6.QtWidgets import (
    QApplication,
    QSplashScreen,
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
from PyQt6.QtCore import QTimer, Qt
from PyQt6 import QtWidgets, uic

import sys
from const import *
from buttons import Buttons
from videos import Video
from showmanager import ShowManager
from editor import Editor
from messageservice import MessagingService
from listsmanager import PlayList
from jsonmanager import JsonManager
import assets_rc


class heart(QMainWindow):
    def __init__(self):
        super().__init__()

        self.SelectedSlide = None
        self.SelectedVideo = None
        self.SelectedPlaylist = None
        self.SelectedSlideshow = None


    
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


        self.action_playlist = QAction("New Playlist", self)
        self.action_slideshow = QAction("New Slideshow", self)

        self.action_lyricshow = QAction("New Lyricsshow", self)
        self.initUI()
        self.lists_manager = PlayList(self, self.items_frame, self.playlists_frame)
        self.buttons = Buttons(self)
        self.videos = Video(self)
        self.show_manager = ShowManager(self)
        self.editor = Editor(self)
        self.message_service = MessagingService()

        self.editor_page.preview_slide.setObjectName("preview_slide")

        # SLIDE FADE
        self.fade_slide.setCheckable(True)
        self.fade_slide.toggled.connect(
            lambda state: self.on_fade_slide_toggled(state)
        )
        self.fade_slide_time.setEnabled(False)

        # VIDEO FADE
        self.fade_background.setCheckable(True)
        self.fade_background.toggled.connect(
            lambda state: self.on_fade_bg_toggled(state)
        )
        self.fade_background_time.setEnabled(False)
        self.show_manager.program_output.add_output(self.program)

       
    def initUI(self):
        
        self.new_list = self.findChild(QToolButton, "new_list")
        New_menu = QMenu(self)



        New_menu.addAction(self.action_playlist)
        New_menu.addAction(self.action_slideshow)
        New_menu.addAction(self.action_lyricshow)

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
    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return

        if hasattr(self, "show_manager"):
            self.show_manager.handle_key(event.key())

        super().keyPressEvent(event)
    def on_fade_slide_toggled(self, state):
        self.fade_slide_time.setEnabled(state)
        self.show_manager.update_fade_button(self.fade_slide, state)


    def on_fade_bg_toggled(self, state):
        self.fade_background_time.setEnabled(state)
        self.show_manager.update_fade_button(self.fade_background, state)

    def resizeEvent(self, event):
        return super().resizeEvent(event)
            
def main():
    app = QApplication(sys.argv)
    pixmap = QPixmap("asset/ui/PresentatorSplash.png")
    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    splash.show()

    splash.showMessage(
        "Starting...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
        Qt.GlobalColor.white
    )
    def start_app():
        
        window = heart()
        splash.finish(window)
        window.show()
        

    QTimer.singleShot(3000, start_app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()