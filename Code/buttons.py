


from preferences import PreferencesWindow
from PyQt6.QtGui import QGuiApplication


class Buttons:
    def __init__(self, parent):
        self.parent = parent
        self.pref_window = parent.pref_window
        self.connect_buttons(parent)
        self.editor_connected = False

    def connect_buttons(self, parent):
        parent.actionQuit.triggered.connect(parent.close)
        parent.actionPreferences.triggered.connect(self.open_preferences)
        parent.editor.clicked.connect(self.open_selected_show)
        parent.actionClose_Editor.triggered.connect(lambda: self.show_editor(False))
        parent.play.clicked.connect(self.start_program)


        parent.actionNew_Playlist.triggered.connect(lambda: parent.lists_manager.add_playlist())
        parent.rename.clicked.connect(lambda: parent.lists_manager.rename())
        parent.action_playlist.triggered.connect(lambda: parent.lists_manager.add_playlist())
        parent.action_slideshow.triggered.connect(lambda: parent.lists_manager.add_slideshow())
        parent.action_lyricshow.triggered.connect(lambda: parent.lists_manager.add_lyricsshow())

        parent.sort_up.clicked.connect(lambda: parent.lists_manager.move_selected_up())
        parent.sort_down.clicked.connect(lambda: parent.lists_manager.move_selected_down())
        
    def connect_pref_buttons(self):
        self.parent.pref_window.close_button.clicked.connect(self.parent.pref_window.close)
        self.parent.pref_window.display_button.clicked.connect(lambda: self.parent.pref_window.display_preferences_page(1))
        self.parent.pref_window.customize_button.clicked.connect(lambda: self.parent.pref_window.display_preferences_page(2))
        self.parent.pref_window.system_button.clicked.connect(lambda: self.parent.pref_window.display_preferences_page(3))


    def connect_editor_buttons(self):
        self.parent.editor_page.NewSlide.clicked.connect(self.parent.editor.add_slide)
        self.parent.editor_page.DeleteSlide.clicked.connect(self.parent.editor.delete_slide)
        self.parent.editor_page.SlideUp.clicked.connect(lambda: self.parent.editor.move_slide("up"))
        self.parent.editor_page.SlideDown.clicked.connect(lambda: self.parent.editor.move_slide("down"))
        self.parent.editor_page.NewText.clicked.connect(self.parent.editor.new_text_element)
        self.parent.editor_page.RenameText.clicked.connect(self.parent.editor.rename_selected)
        self.parent.editor_page.Upload.clicked.connect(self.parent.editor.new_image_element)
        self.parent.editor_page.DeleteElement.clicked.connect(self.parent.editor.delete_selected)
        self.parent.editor_page.ElementUp.clicked.connect(self.parent.editor.move_selected_up)
        self.parent.editor_page.ElementDown.clicked.connect(self.parent.editor.move_selected_down)
        self.parent.editor_page.Center.clicked.connect(self.parent.editor.CenterEvent)
        self.parent.editor_page.Music.clicked.connect(self.parent.editor.cycle_tag)


    def open_preferences(self):
        if self.parent.pref_window is None or not self.parent.pref_window.isVisible():
            self.parent.pref_window = PreferencesWindow(self.parent)
            self.parent.pref_window.manage_window(self.parent.pref_window.settings["display_mode"])
            self.connect_pref_buttons()
        self.parent.pref_window.show()
        self.parent.pref_window.raise_()
        self.parent.pref_window.activateWindow()
    def show_editor(self, state):
        if state == True:
            if not hasattr(self.parent.editor, "current_show"):
                return
            if not self.editor_connected:
                self.connect_editor_buttons()
                self.editor_connected = True
            self.parent.stack.setCurrentWidget(self.parent.editor_page)
            self.parent.actionClose_Editor.setEnabled(True)
            self.parent.editor_page.preview_slide.setStyleSheet("""
                QWidget#preview_slide {
                    background-color: rgba(0,0,0,0);
                    border: 5px solid white;
                    border-image: url(asset/ui/transparent.png) 0 0 0 0 stretch stretch;
                }
            """)

            self.parent.editor_page.setStyleSheet("""
                QWidget#slide_row {
                    background-color: transparent;
                }

                QWidget#slide_row[selected="true"] {
                    background-color: rgb(110,110,110);
                }

                QWidget#slide_row:hover {
                    background-color: rgb(80,80,80);
                }
                """)
        else:
            self.parent.stack.setCurrentWidget(self.parent.main_page)
            self.parent.actionClose_Editor.setEnabled(False)

    def open_selected_show(self):
        show = self.parent.lists_manager.selected_show

        if not show:
            return

        self.parent.editor.load_show(show)
        self.show_editor(True)



    def get_selected_screen(self):
        settings = self.parent.settings

        monitor_name = settings.get("program_monitor", "None")

        if monitor_name == "None":
            return None

        for screen in QGuiApplication.screens():
            if screen.name() == monitor_name:
                return screen

        return None

    def get_selected_screen_lyrics(self):
        settings = self.parent.settings

        name = settings.get("lyrics_monitor", "None")

        if name == "None":
            return None

        for s in QGuiApplication.screens():
            if s.name() == name:
                return s

        return None
    def start_program(self):
        from programshow import ProgramShow

        # 🔁 TOGGLE OFF
        if hasattr(self.parent, "program_window") and self.parent.program_window:
            self.parent.show_manager.program_running = False

            self.parent.program_window.close()
            self.parent.program_window = None
            return

        # 🟢 CREATE WINDOW
        self.parent.program_window = ProgramShow()

        screen = self.get_selected_screen()

        if screen:
            # 👉 siirrä oikealle näytölle
            geometry = screen.geometry()
            self.parent.program_window.setGeometry(geometry)

            # 👉 fullscreen siihen näyttöön
            self.parent.program_window.show()
            self.parent.program_window.windowHandle().setScreen(screen)
            self.parent.program_window.showFullScreen()
        else:
            # 👉 normaali ikkuna
            self.parent.program_window.show()

        self.parent.show_manager.program_running = True

        self.parent.show_manager.program_output.add_output(
            self.parent.program_window
        )

        # 🔥 LYRICS WINDOW
        self.parent.show_manager.update_lyrics_settings()

        if self.parent.show_manager.lyrics_enabled:
            from programshow import LyricsWindow

            self.parent.lyrics_window = LyricsWindow()

            screen = self.get_selected_screen_lyrics()

            if screen:
                geo = screen.geometry()

                self.parent.lyrics_window.setGeometry(geo)
                self.parent.lyrics_window.show()
                self.parent.lyrics_window.windowHandle().setScreen(screen)
                self.parent.lyrics_window.showFullScreen()
            else:
                self.parent.lyrics_window.show()

            # 🔥 LISÄÄ OUTPUT
            self.parent.show_manager.program_output.add_output(
                self.parent.lyrics_window,
                is_lyrics=True
            )