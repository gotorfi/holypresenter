from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QApplication, QHBoxLayout
)
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit

from jsonmanager import JsonManager
import uuid

class PlayList:
    def __init__(self, parent, main_slides_frame: QWidget, playlists_frame: QWidget):
        self.main_slides_frame = main_slides_frame
        self.playlists_frame = playlists_frame
        self.parent = parent

        # Data
        self.playlists = []
        self.slides = []
        self.images = []
        self.songs = []

        # Selected items
        self.selected_playlist = None
        self.selected_show = None
        self.selected_slide = None
        self.selected_song = None
        self.selected_image = None
        self.selected_item = None

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
        for pl in self.playlists:
            if "slides" not in pl:
                pl["slides"] = []

            for show in pl["slides"]:
                if "slides" not in show:
                    show["slides"] = []

        # Initialize playlists frame items
        self.refresh_playlists_frame()
        self.refresh_slides_frame()

    # ---------- ADD ----------
    def add_slideshow(self, name="New Slideshow"):
        if not self.selected_playlist:
            print("No playlist selected")
            return

        item = {
            "type": "slideshow",
            "name": name,
            "slides": []
        }

        self.selected_playlist["slides"].append(item)
        self.json_manager.save(self.playlists, self.slides, self.songs, self.images)
        self.refresh_slides_frame()

    def add_lyricsshow(self, name="New LyricsShow"):
        if not self.selected_playlist:
            return

        item = {
            "type": "lyricsshow",
            "name": name,
            "slides": []
        }

        self.selected_playlist["slides"].append(item)
        self.json_manager.save(self.playlists, self.slides, self.songs, self.images)
        self.refresh_slides_frame()

    def add_playlist(self, name="New Playlist"):
        new_playlist = {
            "id": str(uuid.uuid4()),
            "type": "playlist",
            "name": name,
            "slides": []
        }

        self.playlists.append(new_playlist)
        self.refresh_playlists_frame()


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
        if self.selected_slide and self.selected_playlist:
            self.selected_playlist["slides"].remove(self.selected_slide)
            self.selected_slide = None
            self.refresh_slides_frame()
            self.json_manager.save(self.playlists, [], self.songs, self.images)
    # ---------- RENAME ----------
    def rename(self):
        item = None
        target = None
        list_widget = None

        if self.slides_list.currentItem():
            item = self.slides_list.currentItem()
            index = item.data(Qt.ItemDataRole.UserRole)
            list_widget = self.slides_list

            if not self.selected_playlist:
                return

            slides = self.selected_playlist.get("slides", [])

            if index is None or index >= len(slides):
                return

            target = slides[index]
        elif self.playlists_list.currentItem():
            item = self.playlists_list.currentItem()
            data = item.data(Qt.ItemDataRole.UserRole)

            if not data:
                return

            dtype, value = data

            if dtype == "playlist":
                target = self.get_playlist_by_id(value)
                list_widget = self.playlists_list
            else:
                return

        if not item or not target:
            return

        line_edit = QLineEdit(item.text())
        list_widget.setItemWidget(item, line_edit)

        line_edit.setFocus()
        line_edit.selectAll()

        def finish():
            new_name = line_edit.text().strip() or "Empty"

            target["name"] = new_name
            item.setText(new_name)

            list_widget.removeItemWidget(item)

            self.json_manager.save(self.playlists, [], self.songs, self.images)

            print("RENAMED + SAVED:", target)

        line_edit.returnPressed.connect(finish)

        def on_focus_out(event):
            finish()
            QLineEdit.focusOutEvent(line_edit, event)

        line_edit.focusOutEvent = on_focus_out

    # ---------- MOVE ----------
    def move_slide(self, direction):
        if self.selected_slide and self.selected_playlist:
            slides = self.selected_playlist["slides"]
            idx = slides.index(self.selected_slide)
            new_idx = idx + direction

            if 0 <= new_idx < len(slides):
                slides[idx], slides[new_idx] = slides[new_idx], slides[idx]
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
        self.selected_slide = None
        self.selected_show = None
        self.slides_list.clear()

        if not self.selected_playlist:
            print("NO PLAYLIST SELECTED")
            return

        slides = self.selected_playlist.get("slides", [])
        print("REFRESHING SLIDES:", slides)

        for i, slide in enumerate(slides):
            item = QListWidgetItem(slide['name'])
            item.setData(Qt.ItemDataRole.UserRole, i)

            if slide['type'] == "slideshow":
                item.setIcon(QIcon("asset/ui/slide.png"))
            elif slide['type'] == "lyricsshow":
                item.setIcon(QIcon("asset/ui/lyrics.png"))

            self.slides_list.addItem(item)

    def refresh_playlists_frame(self):
        self.playlists_list.clear()

        # Songs
        for song in self.songs:
            item = QListWidgetItem(song['name'])
            item.setData(Qt.ItemDataRole.UserRole, ("song", song))
            item.setIcon(QIcon("asset/ui/songs.png"))
            self.playlists_list.addItem(item)

        # Images
        for img in self.images:
            item = QListWidgetItem(img['name'])
            item.setData(Qt.ItemDataRole.UserRole, ("image", img))
            item.setIcon(QIcon("asset/ui/upload.png"))
            self.playlists_list.addItem(item)

        # Playlists
        for pl in self.playlists:
            item = QListWidgetItem(pl['name'])
            item.setData(Qt.ItemDataRole.UserRole, ("playlist", pl["id"]))
            item.setIcon(QIcon("asset/ui/playlist.png"))
            self.playlists_list.addItem(item)

    # ---------- CLICK HANDLERS ----------
    def on_slide_clicked(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)

        slides = self.selected_playlist.get("slides", [])
        if index >= len(slides):
            return

        slide = slides[index]
        self.selected_item = None

        if self.selected_show == slide:
            self.selected_slide = None
            item.setBackground(QColor(0,0,0,0))
        else:
            for i in range(self.slides_list.count()):
                self.slides_list.item(i).setBackground(QColor(0,0,0,0))

            self.selected_show = slide
            item.setBackground(QColor(100, 100, 255, 100))

    def on_playlist_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)

        if not data:
            return

        dtype, value = data

        if dtype != "playlist":
            return

        playlist = self.get_playlist_by_id(value)
        if not playlist:
            return

        self.selected_slide = None
        self.selected_playlist = playlist

        for i in range(self.playlists_list.count()):
            self.playlists_list.item(i).setBackground(QColor(0,0,0,0))

        item.setBackground(QColor(100, 100, 255, 100))

        print("NOW SHOWING:", playlist["name"])
        print("SLIDES:", playlist.get("slides", []))

        self.refresh_slides_frame()

    def get_playlist_by_id(self, pid):
        for pl in self.playlists:
            if pl.get("id") == pid:
                return pl
        return None
