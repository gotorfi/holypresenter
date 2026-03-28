import cv2
from PyQt6.QtWidgets import QLabel, QSlider
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QColor, QPen, QPainterPath


class ShowManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.preview_frame = main_window.preview  # QWidget, johon video näytetään
        self.video_label = QLabel(self.preview_frame)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.show()


        # SLIDE OVERLAY
        self.slide_overlay = QLabel(self.preview_frame)
        self.slide_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slide_overlay.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.slide_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.slide_overlay.setStyleSheet("background: transparent;")
        self.slide_overlay.show()

        # Slider ja videolength label main_window:sta
        self.slider: QSlider = main_window.videoslider
        self.length_label: QLabel = main_window.videolength
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider_pressed = False
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.current_frame_index = 0
        self.frame_count = 0
        self.fps = 30

        self.preview_frame.resizeEvent = self.on_resize

    def on_resize(self, event):
        self.video_label.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.slide_overlay.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        return super(type(self.preview_frame), self.preview_frame).resizeEvent(event)

    def play_video(self, path):
        self.stop_video()

        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            print(f"Cannot open video {path}")
            return

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 30

        self.slider.setMaximum(self.frame_count - 1)
        self.slider.setValue(0)

        self.current_frame_index = 0
        self.timer.start(int(1000 / self.fps))
        self.update_length_label()

    def stop_video(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

    def next_frame(self):
        if not self.cap or self.slider_pressed:
            return

        ret, frame = self.cap.read()
        if not ret:
            # loopataan videon alkuun
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_index = 0
            ret, frame = self.cap.read()
            if not ret:
                return

        self.current_frame_index = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.update_slider()
        self.show_frame(frame)

    def show_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        qpix = QPixmap.fromImage(qimg).scaled(
            self.preview_frame.width(),
            self.preview_frame.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(qpix)
        self.update_length_label()

    # 🎛 Slider-logiikka
    def slider_changed(self, value):
        if not self.cap:
            return
        if self.slider_pressed:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)
            ret, frame = self.cap.read()
            if ret:
                self.show_frame(frame)

    def on_slider_pressed(self):
        self.slider_pressed = True

    def on_slider_released(self):
        self.slider_pressed = False
        # kun vapautetaan, jatka playback
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.slider.value())

    def update_slider(self):
        # päivitys vain jos käyttäjä ei skrollaa itse
        if not self.slider_pressed:
            self.slider.setValue(self.current_frame_index)

    def update_length_label(self):
        if not self.cap:
            return
        total_seconds = int(self.frame_count / self.fps)
        current_seconds = int(self.current_frame_index / self.fps)
        total_min, total_sec = divmod(total_seconds, 60)
        curr_min, curr_sec = divmod(current_seconds, 60)
        self.length_label.setText(f"{curr_min:02d}:{curr_sec:02d} / {total_min:02d}:{total_sec:02d}")


    def show_slide(self, slide):
        pix = self.render_slide(slide)
        self.slide_overlay.setPixmap(pix)
    def render_slide(self, slide):
        w = self.preview_frame.width()
        h = self.preview_frame.height()

        BASE_W = 1450
        BASE_H = 825

        scale_x = w / BASE_W
        scale_y = h / BASE_H

        pix = QPixmap(w, h)
        pix.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        for el in slide.get("elements", []):

            x = int(el["x"] * scale_x) - 10
            y = int(el["y"] * scale_y) - 10
            ww = int(el["w"] * scale_x)
            hh = int(el["h"] * scale_y)

            # IMAGE
            if el["type"] == "image":
                img = QPixmap(el["path"])
                if not img.isNull():
                    painter.drawPixmap(
                        x, y,
                        img.scaled(
                            ww, hh,
                            Qt.AspectRatioMode.IgnoreAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    )

            # TEXT
            elif el["type"] == "text":
                text = el.get("text", "")

                font_size = max(6, int(12 * scale_y))
                font = QFont("Arial Black", font_size)
                font.setBold(True)

                painter.setFont(font)
                metrics = QFontMetrics(font)

                lines = text.split("\n")
                line_height = metrics.height()
                total_h = line_height * len(lines)

                start_y = y + (hh - total_h) / 2 + metrics.ascent()

                for i, line in enumerate(lines):
                    if not line:
                        continue

                    tw = metrics.horizontalAdvance(line)
                    tx = int(x + (ww - tw) / 2)
                    ty = int(start_y + i * line_height) + 5

                    path = QPainterPath()
                    path.addText(tx, ty, font, line)

                    # stroke
                    pen = QPen(QColor(0, 0, 0))
                    pen.setWidth(max(4, int(6 * scale_y)))
                    painter.setPen(pen)
                    painter.setBrush(QColor(0, 0, 0))
                    painter.drawPath(path)

                    # fill
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(255, 255, 255))
                    painter.drawPath(path)

        painter.end()

        return pix