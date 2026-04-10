import json

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
from programshow import LyricsWindow
from const import *
from buttons import Buttons
from videos import Video
from showmanager import ShowManager
from editor import Editor
from messageservice import MessagingService
from listsmanager import PlayList
from jsonmanager import JsonManager
try:
    if sys.platform == "darwin":
        import assets_rc_mac as assets_rc
    else:
        import assets_rc
except Exception:
    import assets_rc

from preferences import save_settings
from paths import resource_path



class heart(QMainWindow):
    def __init__(self):
        super().__init__()

        self.SelectedSlide = None
        self.SelectedVideo = None
        self.SelectedPlaylist = None
        self.SelectedSlideshow = None
        self.pref_window = None
        from preferences import load_settings, PreferencesWindow
        self.settings = load_settings()


        uic.loadUi(resource_path("mainpage.ui"), self)
        self.main_page = self.centralWidget()
        self.editor_page = uic.loadUi(resource_path("editor.ui"))
        self.setWindowIcon(QIcon(resource_path("asset/ui/icon.png")))
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

        self.show_manager = ShowManager(self)
        self.pref_window = PreferencesWindow(self)
        self.buttons = Buttons(self)
        self.videos = Video(self)
        
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

        self.fade_slide_time.valueChanged.connect(self.save_fade_times)
        self.fade_background_time.valueChanged.connect(self.save_fade_times)

        self.fade_background.setChecked(self.settings.get("fade_background", False))
        self.fade_background_time.setValue(self.settings.get("fade_background_time", 1))

        self.fade_slide.setChecked(self.settings.get("fade_slide", False))
        self.fade_slide_time.setValue(self.settings.get("fade_slide_time", 1))

        self.notification_input.textChanged.connect(self.update_notification_text)
        self.notification_button.clicked.connect(self.cycle_notification_style)
        self.push_notification.clicked.connect(self.push_notification_live)
        self.clear_notification.clicked.connect(self.clear_notification_live)

        
    def initUI(self):

        self.backgrounds_frame.hide()
        self.upload_background.setEnabled(False)
        
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
        self.settings["fade_slide"] = state
        self.save_settings()


    def on_fade_bg_toggled(self, state):
        self.fade_background_time.setEnabled(state)
        self.show_manager.update_fade_button(self.fade_background, state)

        self.settings["fade_background"] = state
        self.save_settings()
    def resizeEvent(self, event):
        return super().resizeEvent(event)
    def save_fade_times(self):
        self.settings["fade_slide_time"] = self.fade_slide_time.value()
        self.settings["fade_background_time"] = self.fade_background_time.value()
        self.save_settings()


    def save_settings(self):
        save_settings(self.settings)
    def closeEvent(self, event):
        if hasattr(self, "program_window") and self.program_window:
            try:
                self.show_manager.program_running = False
                self.program_window.close()
                self.program_window = None
                
            except Exception as e:
                print("Error closing program window:", e)
        if hasattr(self, "lyrics_window") and self.lyrics_window:
            self.lyrics_window.close()
            self.lyrics_window = None
        event.accept()
    def update_notification_text(self):
        text = self.notification_input.text()

        if len(text) > 50:
            text = text[:50]
            self.notification_input.setText(text)

        self.show_manager.notification_text = text
        self.show_manager.update_layers()


    def cycle_notification_style(self):
        sm = self.show_manager
        sm.notification_style_index = (sm.notification_style_index + 1) % 4
        sm.update_layers()


    def push_notification_live(self):
        self.show_manager.notification_visible = True
        self.show_manager.update_layers()


    def clear_notification_live(self):
        self.show_manager.notification_visible = False
        self.show_manager.update_layers()
        
            
def main():
    app = QApplication(sys.argv)
    pixmap = QPixmap(resource_path("asset/ui/PresentatorSplash.png"))
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