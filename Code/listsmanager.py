from PyQt6.QtWidgets import (
    QAbstractItemView, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QApplication, QHBoxLayout, QGridLayout
)
from PyQt6.QtGui import QDrag, QFont, QFontMetrics, QIcon, QColor, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtCore import QMimeData, QObject, Qt
from PyQt6.QtWidgets import QLineEdit


from messageservice import MessagingService
from jsonmanager import JsonManager
import uuid
import copy


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
class DropIndicator(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(3)
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(100, 100, 255))
        painter.drawRect(self.rect())


class PlaylistListWidget(QListWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        source = event.source()

        # internal reorder
        if source == self:
            super().dropEvent(event)
            return

        item = source.currentItem()
        if not item:
            return

        slide_id = item.data(Qt.ItemDataRole.UserRole)

        old_playlist = self.manager.selected_playlist
        new_playlist = self.manager.hover_playlist

        if not old_playlist or not new_playlist:
            return

        slide = None
        for s in old_playlist["slides"]:
            if s["id"] == slide_id:
                slide = s
                break
        if new_playlist == self.manager.songs_playlist:
            if slide["type"] != "lyricsshow":
                return
        if not slide:
            return

        
        if old_playlist == self.manager.songs_playlist or new_playlist == self.manager.songs_playlist:
            new_slide = copy.deepcopy(slide)
            new_slide["id"] = str(uuid.uuid4())
            new_playlist["slides"].append(new_slide)
        else:
            old_playlist["slides"].remove(slide)
            new_playlist["slides"].append(slide)

        self.manager.refresh_slides_frame()
        self.manager.json_manager.save(
            self.manager.playlists,
            self.manager.slides,
            self.manager.songs,
            self.manager.images
        )

class SlideListWidget(QListWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def dropEvent(self, event):
        source = event.source()

        if source == self:
            super().dropEvent(event)
            return

        item = source.currentItem()
        if not item:
            return

        slide_id = item.data(Qt.ItemDataRole.UserRole)

        old_playlist = None
        for pl in self.manager.playlists:
            if any(s.get("id") == slide_id for s in pl.get("slides", [])):
                old_playlist = pl
                break

        new_playlist = self.manager.hover_playlist

        if not old_playlist or not new_playlist:
            return

        slides = old_playlist["slides"]

        slide = None
        for s in slides:
            if s["id"] == slide_id:
                slide = s
                break

        if not slide:
            return

        if old_playlist == self.manager.songs_playlist or new_playlist == self.manager.songs_playlist:
            new_slide = copy.deepcopy(slide)
            new_slide["id"] = str(uuid.uuid4())
            new_playlist["slides"].append(new_slide)
        else:
            slides.remove(slide)
            new_playlist["slides"].append(slide)
        

        self.manager.refresh_slides_frame()
        self.manager.json_manager.save(
            self.manager.playlists,
            self.manager.slides,
            self.manager.songs,
            self.manager.images
        )

class PlayList(QObject):
    def __init__(self, parent, main_slides_frame: QWidget, playlists_frame: QWidget):
        super().__init__()
        self.main_slides_frame = main_slides_frame
        self.playlists_frame = playlists_frame

        self.slides_items_list = parent.slides_frame
        self.parent = parent
        self.messaging = MessagingService()



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
        self.last_selected_type = None

        self.hover_playlist = None

        # ListWidgets
        self.slides_list = SlideListWidget(self)
        self.playlists_list = PlaylistListWidget(self)

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
        self.playlists_list.model().rowsMoved.connect(self.on_playlist_moved)
        self.slides_list.model().rowsMoved.connect(self.on_slide_moved)


        # PLAYLISTS
        self.playlists_list.setDragEnabled(True)
        self.playlists_list.setAcceptDrops(True)
        self.playlists_list.setDropIndicatorShown(False)  # 🔥 custom viiva
        self.playlists_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.playlists_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        # SLIDES
        self.slides_list.setDragEnabled(True)
        self.slides_list.setAcceptDrops(True)
        self.slides_list.setDropIndicatorShown(False)
        self.slides_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.slides_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        self.playlist_indicator = DropIndicator(self.playlists_list.viewport())
        self.slide_indicator = DropIndicator(self.slides_list.viewport())
        
        self.playlists_list.setMouseTracking(True)
        self.slides_list.setMouseTracking(True)

        self.playlists_list.viewport().installEventFilter(self)
        self.slides_list.viewport().installEventFilter(self)

        self.json_manager = JsonManager()
        saved_data = self.json_manager.load()
        self.playlists = saved_data["playlists"]
        self.slides = saved_data["slides"]
        self.songs = saved_data.get("songs", [])
        self.songs_playlist = {
            "id": "songs_builtin",
            "type": "playlist",
            "name": "Songs",
            "slides": self.songs
        }
        self.images = saved_data["images"]
        for pl in self.playlists:
            if "slides" not in pl:
                pl["slides"] = []

            for show in pl["slides"]:
                if "slides" not in show:
                    show["slides"] = []


        self.backgrounds_playlist = {
            "id": "backgrounds_builtin",
            "type": "backgrounds",
            "name": "Backgrounds"
        }

        self.media_playlist = {
            "id": "media_builtin",
            "type": "media",
            "name": "Media"
        }

        self.selected_special = None
        # Initialize playlists frame items
        self.refresh_playlists_frame()
        self.refresh_slides_frame()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.DragMove:
            pos = event.position().toPoint()

            if obj == self.playlists_list.viewport():
                item = self.playlists_list.itemAt(pos)

                for i in range(self.playlists_list.count()):
                    self.playlists_list.item(i).setBackground(QColor(0,0,0,0))

                if item:
                    item.setBackground(QColor(166, 200, 255))

                    data = item.data(Qt.ItemDataRole.UserRole)
                    if data:
                        if data[0] == "playlist":
                            self.hover_playlist = self.get_playlist_by_id(data[1])
                        elif data[0] == "songs":
                            self.hover_playlist = self.songs_playlist
                        else:
                            self.hover_playlist = None
                    rect = self.playlists_list.visualItemRect(item)
                    self.playlist_indicator.setGeometry(
                        rect.left(),
                        rect.bottom() - 1,
                        rect.width(),
                        3
                    )
                    self.playlist_indicator.show()
                else:
                    self.playlist_indicator.hide()
                    self.hover_playlist = None

            elif obj == self.slides_list.viewport():
                item = self.slides_list.itemAt(pos)

                if item:
                    rect = self.slides_list.visualItemRect(item)
                    self.slide_indicator.setGeometry(
                        rect.left(),
                        rect.bottom() - 1,
                        rect.width(),
                        3
                    )
                    self.slide_indicator.show()
                else:
                    self.slide_indicator.hide()

        elif event.type() == event.Type.DragLeave:
            self.playlist_indicator.hide()
            self.slide_indicator.hide()

            for i in range(self.playlists_list.count()):
                self.playlists_list.item(i).setBackground(QColor(0,0,0,0))

        elif event.type() == event.Type.Drop:
            self.playlist_indicator.hide()
            self.slide_indicator.hide()

            for i in range(self.playlists_list.count()):
                self.playlists_list.item(i).setBackground(QColor(0,0,0,0))

        return super().eventFilter(obj, event)


    # ---------- ADD ----------
    def add_slideshow(self, name="New Slideshow"):
        if self.selected_playlist == self.songs_playlist:
            return
        if not self.selected_playlist:
            return

        item = {
            "id": str(uuid.uuid4()),
            "type": "slideshow",
            "name": name,
            "slides": []
        }

        self.selected_playlist["slides"].append(item)
        self.json_manager.save(self.playlists, self.slides, self.songs, self.images)
        self.refresh_slides_frame()

    def add_lyricsshow(self, name="New LyricsShow"):
        if self.selected_playlist == self.songs_playlist:
            return
        if not self.selected_playlist:
            return

        item = {
            "id": str(uuid.uuid4()),
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
    def delete_selected(self):
        # ---------- DELETE SHOW ----------
        if self.last_selected_type == "show":
                if self.selected_show and self.selected_playlist:

                    if self.selected_playlist == self.songs_playlist:
                        result = self.messaging.show_message(
                            "Confirm Delete",
                            "Are you sure you want to delete this lyrics show from Songs? " \
                            "This action cannot be undone and will remove " \
                            "the lyrics show from the Songs playlist permanently.",
                            options=2
                        )

                        if result != 16384:
                            return

                    try:
                        self.selected_playlist["slides"].remove(self.selected_show)
                    except ValueError:
                        return

                    self.selected_show = None
                    self.refresh_slides_frame()

                    self.json_manager.save(
                        self.playlists,
                        self.slides,
                        self.songs,
                        self.images
                    )
                return

        # ---------- DELETE PLAYLIST ----------
        if self.last_selected_type == "playlist":
            if self.selected_playlist and self.selected_playlist != self.songs_playlist:
                try:
                    self.playlists.remove(self.selected_playlist)
                except ValueError:
                    return

                self.selected_playlist = None
                self.refresh_playlists_frame()
                self.refresh_slides_frame()

                self.json_manager.save(
                    self.playlists,
                    self.slides,
                    self.songs,
                    self.images
                )
    # ---------- RENAME ----------
    def rename(self):
        item = None
        target = None
        list_widget = None

        if self.slides_list.currentItem():
            item = self.slides_list.currentItem()
            list_widget = self.slides_list

            slide_id = item.data(Qt.ItemDataRole.UserRole)

            if not self.selected_playlist:
                return

            slides = self.selected_playlist.get("slides", [])

            target = None
            for s in slides:
                if s["id"] == slide_id:
                    target = s
                    break

            if not target:
                return
        elif self.playlists_list.currentItem():
            item = self.playlists_list.currentItem()
            data = item.data(Qt.ItemDataRole.UserRole)

            if not data:
                return

            dtype, value = data

            if dtype == "songs":
                return

            if dtype == "playlist":
                target = self.get_playlist_by_id(value)
                list_widget = self.playlists_list
            else:
                return

        if not item or not target or not list_widget:
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

        line_edit.returnPressed.connect(finish)

        def on_focus_out(event):
            finish()
            QLineEdit.focusOutEvent(line_edit, event)

        line_edit.focusOutEvent = on_focus_out

    # ---------- MOVE ----------

    def move_selected_up(self):

        if self.last_selected_type == "show":
            if self.selected_show and self.selected_playlist:
                slides = self.selected_playlist["slides"]
                idx = slides.index(self.selected_show)

                if idx > 0:
                    slides[idx], slides[idx - 1] = slides[idx - 1], slides[idx]
                    self.refresh_slides_frame()
            return
        if self.last_selected_type == "playlist":
            if self.selected_playlist and self.selected_playlist != self.songs_playlist:
                idx = self.playlists.index(self.selected_playlist)

                if idx > 0:
                    self.playlists[idx], self.playlists[idx - 1] = self.playlists[idx - 1], self.playlists[idx]
                    self.refresh_playlists_frame()
    def move_selected_down(self):
        if self.last_selected_type == "show":
            if self.selected_show and self.selected_playlist:
                slides = self.selected_playlist["slides"]
                idx = slides.index(self.selected_show)

                if idx < len(slides) - 1:
                    slides[idx], slides[idx + 1] = slides[idx + 1], slides[idx]
                    self.refresh_slides_frame()
            return

        if self.last_selected_type == "playlist":
            if self.selected_playlist and self.selected_playlist != self.songs_playlist:
                idx = self.playlists.index(self.selected_playlist)

                if idx < len(self.playlists) - 1:
                    self.playlists[idx], self.playlists[idx + 1] = self.playlists[idx + 1], self.playlists[idx]
                    self.refresh_playlists_frame()
    def move_slide(self, direction):
        if self.selected_slide and self.selected_playlist:
            slides = self.selected_playlist["slides"]
            idx = slides.index(self.selected_slide)
            new_idx = idx + direction

            if 0 <= new_idx < len(slides):
                slides[idx], slides[new_idx] = slides[new_idx], slides[idx]
                self.refresh_slides_frame()
    def on_playlist_moved(self, parent, start, end, dest, row):
        item = self.playlists.pop(start)

        if row > start:
            row -= 1

        self.playlists.insert(row, item)
    def on_slide_moved(self, parent, start, end, dest, row):
        if not self.selected_playlist:
            return

        slides = self.selected_playlist["slides"]
        item = slides.pop(start)

        if row > start:
            row -= 1

        slides.insert(row, item)
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

        for i, slide in enumerate(slides):
            item = QListWidgetItem(slide['name'])
            item.setData(Qt.ItemDataRole.UserRole, slide["id"])

            if slide['type'] == "slideshow":
                item.setIcon(QIcon("asset/ui/slide.png"))
            elif slide['type'] == "lyricsshow":
                item.setIcon(QIcon("asset/ui/lyrics.png"))

            self.slides_list.addItem(item)

    def refresh_playlists_frame(self):
        self.playlists_list.clear()

        # Songs
        item = QListWidgetItem("Songs")
        item.setData(Qt.ItemDataRole.UserRole, ("songs", "songs_builtin"))
        item.setIcon(QIcon("asset/ui/songs.png"))
        self.playlists_list.addItem(item)

        # Backgrounds
        item = QListWidgetItem("Backgrounds")
        item.setData(Qt.ItemDataRole.UserRole, ("backgrounds", "backgrounds_builtin"))
        item.setIcon(QIcon("asset/ui/backgrounds.png"))
        self.playlists_list.addItem(item)

        # Media
        item = QListWidgetItem("Media")
        item.setData(Qt.ItemDataRole.UserRole, ("media", "media_builtin"))
        item.setIcon(QIcon("asset/ui/Image.png"))
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
        slide_id = item.data(Qt.ItemDataRole.UserRole)

        if not self.selected_playlist:
            return

        slides = self.selected_playlist.get("slides", [])

        slide = None
        for s in slides:
            if s["id"] == slide_id:
                slide = s
                break
        
        if not slide:
            return

        self.selected_item = None
        

        if self.selected_show == slide:
            self.selected_show = None
            item.setBackground(QColor(0, 0, 0, 0))
        else:
            for i in range(self.slides_list.count()):
                self.slides_list.item(i).setBackground(QColor(0, 0, 0, 0))

            self.selected_show = slide
            self.last_selected_type = "show"
            item.setBackground(QColor(100, 100, 255, 100))

        self.show_selected_show_thumbnails()
        self.thumbnail_cache = {}

    def on_playlist_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)

        if not data:
            return
        
        dtype, value = data
        # SPECIAL LISTS
        if dtype == "backgrounds":
            if self.selected_special == "backgrounds":
                self.selected_special = None
                self.parent.backgrounds_frame.hide()
                self.parent.upload_background.setEnabled(False)
                return
            else:
                self.selected_special = "backgrounds"
                self.parent.backgrounds_frame.show()
                self.parent.videos.LoadBackgroundVideos()
                self.parent.upload_background.setEnabled(True)
                return

        elif dtype == "media":
            if self.selected_special == "media":
                self.selected_special = None
                self.parent.backgrounds_frame.hide()
                self.parent.upload_background.setEnabled(False)
                return
            else:
                self.selected_special = "media"
                self.parent.backgrounds_frame.show()
                self.parent.videos.load_media()
                self.parent.upload_background.setEnabled(False)
                return
        if dtype == "songs":
            self.selected_playlist = self.songs_playlist

        elif dtype == "playlist":
            playlist = self.get_playlist_by_id(value)
            if not playlist:
                return
            self.selected_playlist = playlist

        else:
            return
        self.last_selected_type = "playlist"
        self.selected_slide = None

        # UI highlight
        if dtype not in ["backgrounds", "media"]:
            for i in range(self.playlists_list.count()):
                data_i = self.playlists_list.item(i).data(Qt.ItemDataRole.UserRole)
                if data_i and data_i[0] not in ["backgrounds", "media"]:
                    self.playlists_list.item(i).setBackground(QColor(0,0,0,0))

        item.setBackground(QColor(100, 100, 255, 100))

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
            def make_click(s):
                def handler(event):
                    self.selected_slide = s
                    if hasattr(self.parent, "show_manager"):
                        self.parent.show_manager.show_slide(s)
                return handler

            card.mousePressEvent = make_click(slide)
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