from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QApplication, QHBoxLayout
)
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit

from jsonmanager import JsonManager

class PlayList:
    def __init__(self, main_slides_frame: QWidget, playlists_frame: QWidget):
        self.main_slides_frame = main_slides_frame
        self.playlists_frame = playlists_frame

        # Data
        self.playlists = []
        self.slides = []
        self.images = []
        self.songs = []

        # Selected items
        self.selected_playlist = None
        self.selected_slide = None
        self.selected_song = None
        self.selected_image = None

        # ListWidgets
        self.slides_list = QListWidget()
        self.playlists_list = QListWidget()

        # Layout
        slides_layout = QVBoxLayout()
        slides_layout.addWidget(self.slides_list)
        self.main_slides_frame.setLayout(slides_layout)

        playlists_layout = QVBoxLayout()
        playlists_layout.addWidget(self.playlists_list)
        self.playlists_frame.setLayout(playlists_layout)

        # Connect signals
        self.slides_list.itemClicked.connect(self.on_slide_clicked)
        self.playlists_list.itemClicked.connect(self.on_playlist_clicked)

        
        self.json_manager = JsonManager()
        saved_data = self.json_manager.load()
        self.playlists = saved_data["playlists"]
        self.slides = saved_data["slides"]
        self.songs = saved_data["songs"]
        self.images = saved_data["images"]

        # Initialize playlists frame items
        self.refresh_playlists_frame()
        self.refresh_slides_frame()

    # ---------- ADD ----------
    def add_slideshow(self, name="New Slideshow"):
        item = {"type": "slideshow", "name": name}
        self.slides.append(item)
        self.refresh_slides_frame()

    def add_lyricsshow(self, name="New LyricsShow"):
        item = {"type": "lyricsshow", "name": name}
        self.slides.append(item)
        self.refresh_slides_frame()
    def add_playlist(self, name="New Playlist"):
        new_playlist = {"type": "playlist", "name": name, "slides": []}
        self.playlists.append(new_playlist)
        self.refresh_playlists_frame()
        for i in range(self.playlists_list.count()):
            item = self.playlists_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == new_playlist:
                self.playlists_list.setCurrentItem(item)
                self.selected_item = new_playlist
                self.rename()
                break
    def add_image(self, image_name):
        self.images.append({"type": "image", "name": image_name})
        self.refresh_playlists_frame()
        # Enable/Disable buttons for image actions
        # Enable here

    def add_song(self, song_name):
        self.songs.append({"type": "song", "name": song_name})
        self.refresh_playlists_frame()
        # Enable/Disable buttons for song actions
        # Enable here

    # ---------- REMOVE ----------
    def delete_playlist(self):
        if self.selected_playlist:
            self.playlists.remove(self.selected_playlist)
            self.selected_playlist = None
            self.refresh_playlists_frame()

    def delete_slide(self):
        if self.selected_slide:
            self.slides.remove(self.selected_slide)
            self.selected_slide = None
            self.refresh_slides_frame()

    # ---------- RENAME ----------
    def rename(self):
        list_widget = None
        target = None

        if self.selected_slide:
            list_widget = self.slides_list
            target = self.selected_slide
        elif getattr(self, 'selected_item', None):
            list_widget = self.playlists_list
            target = self.selected_item
        else:
            return

        # Etsi vastaava QListWidgetItem
        current_item = None
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == target:
                current_item = item
                break

        if not current_item:
            return

        # Luo QLineEdit
        line_edit = QLineEdit(current_item.text())
        list_widget.setItemWidget(current_item, line_edit)
        line_edit.setFocus()
        line_edit.selectAll()

        def finish():
            new_name = line_edit.text().strip()
            if not new_name:
                new_name = "Empty"

            target['name'] = new_name

            current_item.setText(new_name)
            list_widget.removeItemWidget(current_item)

        line_edit.returnPressed.connect(finish)

        def on_focus_out(event):
            finish()
            QLineEdit.focusOutEvent(line_edit, event)

        line_edit.focusOutEvent = on_focus_out
        self.json_manager.save(self.playlists, self.slides, self.songs, self.images)

    # ---------- MOVE ----------
    def move_slide(self, direction):
        if self.selected_slide:
            idx = self.slides.index(self.selected_slide)
            new_idx = idx + direction
            if 0 <= new_idx < len(self.slides):
                self.slides[idx], self.slides[new_idx] = self.slides[new_idx], self.slides[idx]
                self.refresh_slides_frame()

    def move_playlist(self, direction):
        if self.selected_playlist:
            idx = self.playlists.index(self.selected_playlist)
            new_idx = idx + direction
            if 0 <= new_idx < len(self.playlists):
                self.playlists[idx], self.playlists[new_idx] = self.playlists[new_idx], self.playlists[idx]
                self.refresh_playlists_frame()

    # ---------- REFRESH UI ----------
    def refresh_slides_frame(self):
        self.slides_list.clear()
        for slide in self.slides:
            item = QListWidgetItem(slide['name'])
            item.setData(Qt.ItemDataRole.UserRole, slide)
            if slide['type'] == "slideshow":
                item.setIcon(QIcon("asset/ui/slide.png"))
            elif slide['type'] == "lyricsshow":
                item.setIcon(QIcon("asset/ui/lyrics.png"))
            elif slide['type'] == "playlist":
                item.setIcon(QIcon("asset/ui/playlist.png"))
            self.slides_list.addItem(item)

    def refresh_playlists_frame(self):
        self.playlists_list.clear()

        # Songs
        for song in self.songs:
            item = QListWidgetItem(song['name'])
            item.setData(Qt.ItemDataRole.UserRole, song)
            item.setIcon(QIcon("asset/ui/songs.png"))
            self.playlists_list.addItem(item)

        # Images
        for img in self.images:
            item = QListWidgetItem(img['name'])
            item.setData(Qt.ItemDataRole.UserRole, img)
            item.setIcon(QIcon("asset/ui/upload.png"))
            self.playlists_list.addItem(item)

        # Playlists
        for pl in self.playlists:
            item = QListWidgetItem(pl['name'])
            item.setData(Qt.ItemDataRole.UserRole, pl)
            item.setIcon(QIcon("asset/ui/playlist.png"))
            self.playlists_list.addItem(item)

    # ---------- CLICK HANDLERS ----------
    def on_slide_clicked(self, item):
        slide = item.data(Qt.ItemDataRole.UserRole)
        self.selected_item = None

        if self.selected_slide == slide:
            self.selected_slide = None
            item.setBackground(QColor(0,0,0,0))
        else:
            for i in range(self.slides_list.count()):
                self.slides_list.item(i).setBackground(QColor(0,0,0,0))

            self.selected_slide = slide
            item.setBackground(QColor(100, 100, 255, 100))

    def on_playlist_clicked(self, item):
        clicked = item.data(Qt.ItemDataRole.UserRole)


        self.selected_slide = None

        if getattr(self, 'selected_item', None) == clicked:
            self.selected_item = None
            item.setBackground(QColor(0,0,0,0))
            return

        for i in range(self.playlists_list.count()):
            self.playlists_list.item(i).setBackground(QColor(0,0,0,0))

        self.selected_item = clicked
        item.setBackground(QColor(100, 100, 255, 100))