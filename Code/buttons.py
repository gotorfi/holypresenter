


from preferences import PreferencesWindow


class Buttons:
    def __init__(self, parent):
        self.parent = parent
        self.pref_window = None
        self.connect_buttons(parent)

    def connect_buttons(self, parent):
        parent.actionQuit.triggered.connect(parent.close)
        parent.actionPreferences.triggered.connect(self.open_preferences)
        parent.editor.clicked.connect(lambda: self.show_editor(True))
        parent.actionClose_Editor.triggered.connect(lambda: self.show_editor(False))
    def connect_pref_buttons(self):
        self.pref_window.close_button.clicked.connect(self.pref_window.close)
        self.pref_window.display_button.clicked.connect(lambda: self.pref_window.display_preferences_page(1))
        self.pref_window.customize_button.clicked.connect(lambda: self.pref_window.display_preferences_page(2))
        self.pref_window.system_button.clicked.connect(lambda: self.pref_window.display_preferences_page(3))
        self.pref_window.diplay_options.currentIndexChanged.connect(lambda: self.pref_window.manage_window(self.pref_window.diplay_options.currentText().lower()))
        self.pref_window.restore_button.clicked.connect(lambda: self.pref_window.RESTORE())


    def open_preferences(self):
        if self.pref_window is None or not self.pref_window.isVisible():
            self.pref_window = PreferencesWindow(self.parent)
            self.connect_pref_buttons()
        self.pref_window.show()
        self.pref_window.raise_()
        self.pref_window.activateWindow()
    def show_editor(self, state):
        if state == True:
            self.parent.stack.setCurrentWidget(self.parent.editor_page)
            self.parent.actionClose_Editor.setEnabled(True)
        else:
            self.parent.stack.setCurrentWidget(self.parent.main_page)
            self.parent.actionClose_Editor.setEnabled(False)