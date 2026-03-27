


from preferences import PreferencesWindow


class Buttons:
    def __init__(self, parent):
        self.parent = parent
        self.pref_window = None
        self.connect_buttons(parent)
        self.editor_connected = False

    def connect_buttons(self, parent):
        parent.actionQuit.triggered.connect(parent.close)
        parent.actionPreferences.triggered.connect(self.open_preferences)
        parent.editor.clicked.connect(self.open_selected_show)
        parent.actionClose_Editor.triggered.connect(lambda: self.show_editor(False))


        parent.actionNew_Playlist.triggered.connect(lambda: parent.lists_manager.add_playlist())
        parent.rename.clicked.connect(lambda: parent.lists_manager.rename())
        parent.action_playlist.triggered.connect(lambda: parent.lists_manager.add_playlist())
        parent.action_slideshow.triggered.connect(lambda: parent.lists_manager.add_slideshow())
        parent.action_lyricshow.triggered.connect(lambda: parent.lists_manager.add_lyricsshow())
        
    def connect_pref_buttons(self):
        self.pref_window.close_button.clicked.connect(self.pref_window.close)
        self.pref_window.display_button.clicked.connect(lambda: self.pref_window.display_preferences_page(1))
        self.pref_window.customize_button.clicked.connect(lambda: self.pref_window.display_preferences_page(2))
        self.pref_window.system_button.clicked.connect(lambda: self.pref_window.display_preferences_page(3))
        self.pref_window.diplay_options.currentIndexChanged.connect(lambda: self.pref_window.manage_window(self.pref_window.diplay_options.currentText().lower()))
        self.pref_window.restore_button.clicked.connect(lambda: self.pref_window.RESTORE())


    def connect_editor_buttons(self):
        self.parent.editor_page.NewSlide.clicked.connect(self.parent.editor.add_slide)
        self.parent.editor_page.DeleteSlide.clicked.connect(self.parent.editor.delete_slide)
        self.parent.editor_page.SlideUp.clicked.connect(lambda: self.parent.editor.move_slide("up"))
        self.parent.editor_page.SlideDown.clicked.connect(lambda: self.parent.editor.move_slide("down"))
        self.parent.editor_page.NewText.clicked.connect(self.parent.editor.new_text_element)
        #self.parent.editor_page.DeleteElement.clicked.connect(self.parent.editor.delete_selected)
        self.parent.editor_page.RenameText.clicked.connect(self.parent.editor.rename_selected)
        self.parent.editor_page.Upload.clicked.connect(self.parent.editor.new_image_element)
        self.parent.editor_page.DeleteElement.clicked.connect(self.parent.editor.delete_selected)
        self.parent.editor_page.ElementUp.clicked.connect(self.parent.editor.move_selected_up)
        self.parent.editor_page.ElementDown.clicked.connect(self.parent.editor.move_selected_down)
        self.parent.editor_page.Center.clicked.connect(self.parent.editor.CenterEvent)
        self.parent.editor_page.Music.clicked.connect(self.parent.editor.cycle_tag)


    def open_preferences(self):
        if self.pref_window is None or not self.pref_window.isVisible():
            self.pref_window = PreferencesWindow(self.parent)
            self.connect_pref_buttons()
        self.pref_window.show()
        self.pref_window.raise_()
        self.pref_window.activateWindow()
    def show_editor(self, state):
        if state == True:
            if not hasattr(self.parent.editor, "current_show"):
                print("No show loaded")
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
            print("No show selected")
            return

        self.parent.editor.load_show(show)
        self.show_editor(True)