from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QApplication, QHBoxLayout, QGridLayout
)
from PyQt6.QtGui import QFont, QFontMetrics, QIcon, QColor, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit

from jsonmanager import JsonManager
import uuid


TAG_COLORS = {
    "Verse1": (125, 105, 255),
    "Verse2": (125, 105, 255),
    "Verse3": (125, 105, 255),
    "Verse4": (125, 105, 255),
    "PreChorus1": (255, 102, 204),
    "PreChorus2": (255, 102, 204),
    "Chorus1": (255, 74, 74),
    "Chorus2": (255, 74, 74),
    "Bridge": (255, 183, 89),
    None: (150, 150, 150)
}


class PlayList:
    def __init__(self, parent, main_slides_frame: QWidget, playlists_frame: QWidget):
        self.main_slides_frame = main_slides_frame
        self.playlists_frame = playlists_frame

        self.slides_items_list = parent.slides_frame
        self.parent = parent

        # Data
        self.playlists = []
        self.slides = []
        self.images = []
        self.songs = []
        self.thumbnail_cache = {}

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
        self.show_selected_show_thumbnails()
        self.thumbnail_cache = {}

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


    def get_tag_color(self, tag):
        return TAG_COLORS.get(tag, (150, 150, 150))
    
    def show_selected_show_thumbnails(self):
        scroll_area = self.slides_items_list

        # ---------- INIT ----------
        if not hasattr(scroll_area, 'container_widget'):
            scroll_area.container_widget = QWidget()
            scroll_area.setWidget(scroll_area.container_widget)
            scroll_area.setWidgetResizable(True)

        container = scroll_area.container_widget

        # ---------- CLEAR ----------
        layout = container.layout()
        if layout is None:
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            container.setLayout(layout)
        else:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    while item.layout().count():
                        sub = item.layout().takeAt(0)
                        if sub.widget():
                            sub.widget().deleteLater()

        if not self.selected_show:
            return

        slides = self.selected_show.get("slides", [])

        # ---------- GRID ----------
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(grid)

        # ---------- SIZE ----------
        cols = 3
        spacing = 10
        viewport_width = scroll_area.viewport().width()

        thumb_w = (viewport_width - (cols + 1) * spacing) // cols
        thumb_h = int(thumb_w * 9 / 16)

        # 🔥 SUPER RENDER (vain terävyyteen)
        SUPER_SCALE = 2
        render_w = thumb_w * SUPER_SCALE
        render_h = thumb_h * SUPER_SCALE
        BASE_W = 1450
        BASE_H = 825

        scale_x = render_w / BASE_W
        scale_y = render_h / BASE_H

        # ---------- LOOP ----------
        for idx, slide in enumerate(slides):
            row = idx // cols
            col = idx % cols

            tag = slide.get("tag")
            r, g, b = self.get_tag_color(tag)

            pix = QPixmap(render_w, render_h)

            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            # ---------- BACKGROUND ----------
            bg = QPixmap("asset/ui/transparent.png")
            painter.drawPixmap(0, 0, render_w, render_h, bg)

            for el in slide.get("elements", []):
                x = int(el["x"] * scale_x) - 10
                y = int(el["y"] * scale_y) - 10
                w = int(el["w"] * scale_x)
                h = int(el["h"] * scale_y)

                # ---------- IMAGE ----------
                if el["type"] == "image":
                    img = QPixmap(el["path"])
                    if not img.isNull():
                        painter.drawPixmap(
                            x, y,
                            img.scaled(
                                w, h,
                                Qt.AspectRatioMode.IgnoreAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                        )

                # ---------- TEXT ----------
                elif el["type"] == "text":
                    text = el.get("text", "")

                    # 🔥 fontti
                    font_size = max(14, int(24 * scale_y))
                    font = QFont("Arial Black", font_size)
                    font.setBold(True)
                    font.setWeight(QFont.Weight.Black)

                    painter.setFont(font)
                    metrics = QFontMetrics(font)

                    # =========================
                    # 🔥 LINE BREAK HANDLING
                    # =========================
                    lines = text.split("\n")

                    line_height = metrics.height()
                    total_h = line_height * len(lines)

                    start_y = y + (h - total_h) / 2 + metrics.ascent()

                    for i, line in enumerate(lines):
                        if not line:
                            continue

                        tw = metrics.horizontalAdvance(line)

                        tx = int(x + (w - tw) / 2)
                        ty = int(start_y + i * line_height)

                        # =========================
                        # 🔥 TRUE STROKE PATH
                        # =========================
                        path = QPainterPath()
                        path.addText(tx, ty, font, line)

                        pen = QPen(QColor(0, 0, 0))
                        pen.setWidth(max(8, int(12 * scale_y)))
                        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                        pen.setCapStyle(Qt.PenCapStyle.RoundCap)

                        painter.setPen(pen)
                        painter.setBrush(QColor(0, 0, 0))
                        painter.drawPath(path)

                        # =========================
                        # 🔥 FILL TEXT
                        # =========================
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(QColor(255, 255, 255))
                        painter.drawPath(path)
            painter.end()

            # ---------- DOWNSCALE ----------
            final_pix = pix.scaled(
                thumb_w, thumb_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # ---------- UI ----------
            card = QWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(0)

            thumb = QLabel()
            thumb.setPixmap(final_pix)
            thumb.setFixedSize(thumb_w, thumb_h)

            thumb.setStyleSheet(f"""
                border: 3px solid rgb({r},{g},{b});
            """)

            card_layout.addWidget(thumb)

            tag_bar = QLabel(tag or "")
            tag_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tag_bar.setFixedHeight(22)

            tag_bar.setStyleSheet(f"""
                background-color: rgb({r},{g},{b});
                font-weight: bold;
                border: none;
            """)

            card_layout.addWidget(tag_bar)

            grid.addWidget(card, row, col)

        # ---------- RESIZE ----------
        scroll_area.resizeEvent = lambda e: self.show_selected_show_thumbnails()