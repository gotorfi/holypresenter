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
import assets_rc

import json
import os
from PyQt6.QtGui import QGuiApplication

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

        self.settings = {}
        self.load_settings()
        self.populate_monitors()
        self.apply_settings_to_ui()
        self.connect_signals()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = DEFAULT_SETTINGS.copy()
            self.save_settings()


    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

    def populate_monitors(self):
        self.ProgramOutputMonitor.clear()
        self.LyricsOutputMonitor.clear()

        self.ProgramOutputMonitor.addItem("None")
        self.LyricsOutputMonitor.addItem("None")

        screens = QGuiApplication.screens()

        for screen in screens:
            name = screen.name()
            self.ProgramOutputMonitor.addItem(name)
            self.LyricsOutputMonitor.addItem(name)
    def set_combobox_safe(self, box, value):
        index = box.findText(value)
        if index >= 0:
            box.setCurrentIndex(index)
        else:
            box.setCurrentIndex(0)
    def connect_signals(self):
        self.diplay_options.currentTextChanged.connect(self.on_display_changed)
        self.ProgramOutputMonitor.currentTextChanged.connect(self.on_program_monitor_changed)
        self.LyricsOutputMonitor.currentTextChanged.connect(self.on_lyrics_monitor_changed)

        self.enable_lyrics.toggled.connect(self.on_enable_lyrics)

        self.lyrics_one_third.currentTextChanged.connect(self.on_position_changed)
        self.background_color.currentTextChanged.connect(self.on_color_changed)

        self.restore_button.clicked.connect(self.RESTORE)

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
        if self.message_service.show_message(
            "Restore Defaults",
            "Are you sure you want to restore default settings?\nThis cannot be undone.",
            options=2,
            icon=QMessageBox.Icon.Warning
        ) == QMessageBox.StandardButton.Yes:

            self.settings = DEFAULT_SETTINGS.copy()
            self.save_settings()

            self.populate_monitors()
            self.apply_settings_to_ui()
            
    def apply_settings_to_ui(self):
        s = self.settings

        # Display mode
        index = self.diplay_options.findText(s["display_mode"].capitalize())
        if index >= 0:
            self.diplay_options.setCurrentIndex(index)

        # Monitors
        self.set_combobox_safe(self.ProgramOutputMonitor, s["program_monitor"])
        self.set_combobox_safe(self.LyricsOutputMonitor, s["lyrics_monitor"])

        # Lyrics enable
        self.enable_lyrics.setChecked(s["enable_lyrics"])

        # Position
        self.set_combobox_safe(self.lyrics_one_third, s["lyrics_position"])

        # Color
        self.set_combobox_safe(self.background_color, s["background_color"])

        self.update_lyrics_enabled_state()
        self.update_color_preview()
        self.update_position_preview()

        available = [self.ProgramOutputMonitor.itemText(i) for i in range(self.ProgramOutputMonitor.count())]

        if self.settings["program_monitor"] not in available:
            self.settings["program_monitor"] = "None"

        if self.settings["lyrics_monitor"] not in available:
            self.settings["lyrics_monitor"] = "None"

        self.save_settings()

    def update_lyrics_enabled_state(self):
        enabled = self.enable_lyrics.isChecked()

        self.lyrics_one_third.setEnabled(enabled)
        self.background_color.setEnabled(enabled)
    def update_color_preview(self):
        color_map = {
            "Green": "rgb(0,255,0)",
            "Blue": "rgb(0,0,255)",
            "Red": "rgb(255,0,0)",
            "Yellow": "rgb(255,255,0)"
        }

        color = self.settings.get("background_color", "Green")
        css = color_map.get(color, "rgb(0,255,0)")

        self.color_bg_preview.setStyleSheet(f"background-color: {css};")
    def update_position_preview(self):
        pos = self.settings.get("lyrics_position", "Down")

        text_map = {
            "Up": "TOP",
            "Center": "CENTER",
            "Down": "BOTTOM"
        }

        self.preview_lyrics_pos.setText(text_map.get(pos, "BOTTOM"))

    def on_display_changed(self, value):
        value = value.lower()
        self.settings["display_mode"] = value
        self.save_settings()
        self.manage_window(value)
    def on_program_monitor_changed(self, value):
        self.settings["program_monitor"] = value
        self.save_settings()
    def on_lyrics_monitor_changed(self, value):
        self.settings["lyrics_monitor"] = value
        self.save_settings()
    def on_enable_lyrics(self, state):
        self.settings["enable_lyrics"] = state
        self.save_settings()
        self.update_lyrics_enabled_state()
    def on_position_changed(self, value):
        self.settings["lyrics_position"] = value
        self.save_settings()
        self.update_position_preview()
    def on_color_changed(self, value):
        self.settings["background_color"] = value
        self.save_settings()
        self.update_color_preview()