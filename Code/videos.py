import os
from zipfile import Path
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import cv2
import math


class Video:
    def __init__(self, parent):
        self.parent = parent
        self.bg_thumbnails = []
        self.media_thumbnails = []
        self.LoadBackgroundVideos()

    def on_thumbnail_clicked(self, video_path):
        self.parent.show_manager.play_video(video_path)

    def get_video_duration(self, path):
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        if fps > 0:
            seconds = int(frames / fps)
            return f"{seconds // 60}:{seconds % 60:02d}"
        return "0:00"

    def get_thumbnail(self, path):
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        frame = cv2.resize(frame, (160, 90))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def LoadBackgroundVideos(self):
        scroll = self.parent.backgrounds_frame
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        base = Path(__file__).resolve().parent
        folder = base / "savecloud" / "backgrounds"
        if not os.path.exists(folder):
            return

        # 🔥 ERILLINEN LISTA
        self.bg_thumbnails = []

        content = scroll.widget()
        if content is None:
            content = QWidget()
            scroll.setWidget(content)
            scroll.setWidgetResizable(True)
        layout = content.layout()
        if layout is None:
            layout = QGridLayout()
            content.setLayout(layout)

        # 🔥 CLEAR
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        files = [f for f in os.listdir(folder) if f.endswith((".mp4", ".mov", ".avi"))]

        cols = 6

        def resize_thumbnails():
            total_width = scroll.viewport().width()
            spacing = layout.spacing()
            margins = layout.contentsMargins()

            available_width = total_width - margins.left() - margins.right() - (cols - 1) * spacing
            card_width = math.floor(available_width / cols)

            for i in range(layout.count()):
                card = layout.itemAt(i).widget()
                if not card:
                    continue

                card.setFixedWidth(card_width)

                thumb_label = card.layout().itemAt(0).widget()
                thumb_height = int(card_width * 9 / 16)

                if i >= len(self.bg_thumbnails):
                    continue

                pixmap = self.bg_thumbnails[i]

                scaled = pixmap.scaled(
                    card_width,
                    thumb_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                thumb_label.setFixedHeight(thumb_height)
                thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb_label.setPixmap(scaled)

        # 🔹 BUILD UI
        for i, file in enumerate(files):
            path = os.path.join(folder, file)
            row = i // cols
            col = i % cols

            card = QWidget()
            vbox = QVBoxLayout()
            vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
            vbox.setSpacing(2)
            card.setLayout(vbox)

            pixmap = self.get_thumbnail(path)

            if pixmap is None or pixmap.isNull():
                pixmap = QPixmap(160, 90)
                pixmap.fill(Qt.GlobalColor.black)

            self.bg_thumbnails.append(pixmap)

            thumb_label = QLabel()
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_label.setStyleSheet("background: black;")
            vbox.addWidget(thumb_label)

            thumb_label.mousePressEvent = lambda event, path=path: self.on_thumbnail_clicked(path)

            name_label = QLabel(file)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            vbox.addWidget(name_label)

            duration = self.get_video_duration(path)
            duration_label = QLabel(duration)
            duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(duration_label)

            layout.addWidget(card, row, col)

        def on_resize(event):
            resize_thumbnails()
            return QWidget.resizeEvent(scroll, event)

        scroll.resizeEvent = on_resize
        resize_thumbnails()

    def load_media(self):
        scroll = self.parent.backgrounds_frame
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        base = Path(__file__).resolve().parent
        folder = base / "savecloud" / "media"
        if not os.path.exists(folder):
            os.makedirs(folder)

        # 🔥 ERILLINEN LISTA
        self.media_thumbnails = []

        content = scroll.widget()
        if content is None:
            content = QWidget()
            scroll.setWidget(content)
            scroll.setWidgetResizable(True)
        layout = content.layout()
        if layout is None:
            layout = QGridLayout()
            content.setLayout(layout)

        # 🔥 CLEAR
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        files = [f for f in os.listdir(folder) if f.lower().endswith(
            (".mp4", ".mov", ".avi", ".png", ".jpg", ".jpeg")
        )]

        cols = 6

        def resize_thumbnails():
            total_width = scroll.viewport().width()
            spacing = layout.spacing()
            margins = layout.contentsMargins()

            available_width = total_width - margins.left() - margins.right() - (cols - 1) * spacing
            card_width = math.floor(available_width / cols)

            for i in range(layout.count()):
                card = layout.itemAt(i).widget()
                if not card:
                    continue

                card.setFixedWidth(card_width)

                thumb_label = card.layout().itemAt(0).widget()
                thumb_height = int(card_width * 9 / 16)

                if i >= len(self.media_thumbnails):
                    continue

                pixmap = self.media_thumbnails[i]

                scaled = pixmap.scaled(
                    card_width,
                    thumb_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                thumb_label.setFixedHeight(thumb_height)
                thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb_label.setPixmap(scaled)

        # 🔹 BUILD UI
        for i, file in enumerate(files):
            path = os.path.join(folder, file)
            row = i // cols
            col = i % cols

            card = QWidget()
            vbox = QVBoxLayout()
            vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
            vbox.setSpacing(2)
            card.setLayout(vbox)

            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                pixmap = QPixmap(path)
            else:
                pixmap = self.get_thumbnail(path)

            if pixmap is None or pixmap.isNull():
                pixmap = QPixmap(160, 90)
                pixmap.fill(Qt.GlobalColor.black)

            self.media_thumbnails.append(pixmap)

            thumb_label = QLabel()
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_label.setStyleSheet("background: black;")
            vbox.addWidget(thumb_label)

            thumb_label.mousePressEvent = lambda event, path=path: self.on_thumbnail_clicked(path)

            name_label = QLabel(file)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            vbox.addWidget(name_label)

            if file.lower().endswith((".mp4", ".mov", ".avi")):
                duration = self.get_video_duration(path)
            else:
                duration = ""

            duration_label = QLabel(duration)
            duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(duration_label)

            layout.addWidget(card, row, col)

        def on_resize(event):
            resize_thumbnails()
            return QWidget.resizeEvent(scroll, event)

        scroll.resizeEvent = on_resize
        resize_thumbnails()