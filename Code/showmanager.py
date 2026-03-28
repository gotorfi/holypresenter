import cv2
from PyQt6.QtWidgets import QLabel, QSlider
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QColor, QPen, QPainterPath
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation


class ShowManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.preview_frame = main_window.preview  # QWidget, johon video näytetään
        self.video_label = QLabel(self.preview_frame)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.show()



        self.video_label_next = QLabel(self.preview_frame)
        self.video_label_next.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.video_label_next.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label_next.hide()

        self.video_opacity = QGraphicsOpacityEffect()
        self.video_label_next.setGraphicsEffect(self.video_opacity)
        self.video_opacity.setOpacity(0.0)
        self.cap_next = None

        # SLIDE OVERLAY
        self.slide_overlay = QLabel(self.preview_frame)
        self.slide_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slide_overlay.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.slide_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.slide_overlay.setStyleSheet("background: transparent;")
        self.slide_overlay.show()

        
        self.slide_opacity = QGraphicsOpacityEffect()
        self.slide_overlay.setGraphicsEffect(self.slide_opacity)
        self.slide_opacity.setOpacity(1.0)

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
        self.video_enabled = True
        self.slide_enabled = True
        self.current_slide = None
        self.current_video_path = None

        self.preview_frame.resizeEvent = self.on_resize

    def on_resize(self, event):
        self.video_label.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.slide_overlay.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        return super(type(self.preview_frame), self.preview_frame).resizeEvent(event)

    def play_video(self, path):
        fade_on = self.main_window.fade_background.isChecked()
        duration = self.main_window.fade_background_time.value()

        self.current_video_path = path
        self.video_enabled = True

        # =====================================
        # 🔥 FADE MODE (CROSSFADE)
        # =====================================
        if fade_on and self.cap is not None:

            self.cap_next = cv2.VideoCapture(path)

            if not self.cap_next.isOpened():
                print(f"Cannot open video {path}")
                return
            self.video_label_next.show()


            def update_next_frame():
                if not self.cap_next:
                    return

                ret, frame = self.cap_next.read()
                if not ret:
                    self.cap_next.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    return

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w

                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pix = QPixmap.fromImage(qimg).scaled(
                    self.preview_frame.width(),
                    self.preview_frame.height(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )

                self.video_label_next.setPixmap(pix)


            try:
                self.timer.timeout.disconnect()
            except:
                pass

            self.timer.timeout.connect(self.next_frame)
            self.timer.timeout.connect(update_next_frame)

            self.video_anim = QPropertyAnimation(self.video_opacity, b"opacity")
            self.video_anim.setDuration(int(duration * 1000))
            self.video_anim.setStartValue(0.0)
            self.video_anim.setEndValue(1.0)

            def finish():
                self.cap = self.cap_next
                self.cap_next = None

                self.video_label.setPixmap(self.video_label_next.pixmap())
                self.video_label_next.hide()
                self.video_opacity.setOpacity(0.0)

                try:
                    self.timer.timeout.disconnect(update_next_frame)
                except:
                    pass

            self.video_anim.finished.connect(finish)
            self.video_anim.start()

            return

        # =====================================
        # 🔧 NORMAALI MODE (ei fade)
        # =====================================

        self.video_label.clear()
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
        self.update_layers()

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

    def update_layers(self):
        # VIDEO
        if self.video_enabled:
            self.video_label.show()
        else:
            self.video_label.clear()
            self.video_label.hide()
            

        # SLIDE
        if self.slide_enabled and self.current_slide:
            pix = self.render_slide(self.current_slide)
            self.slide_overlay.setPixmap(pix)
            self.slide_overlay.show()
        else:
            self.slide_overlay.clear()
            self.slide_overlay.hide()
    def show_slide(self, slide):
        fade_on = self.main_window.fade_slide.isChecked()
        duration = self.main_window.fade_slide_time.value()

        self.current_slide = slide
        self.slide_enabled = True

        pix = self.render_slide(slide)
        self.slide_overlay.setPixmap(pix)
        self.slide_overlay.show()

        if fade_on:
            self.slide_opacity.setOpacity(0.0)
            self.fade_slide_in(duration)
        else:
            self.slide_opacity.setOpacity(1.0)
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
    

    def update_fade_button(self, btn, enabled):
        if enabled:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(100, 100, 255);
                    border: 1px solid rgba(255, 255, 255, 80);
                    border-radius: 6px;
                    padding: 3px;
                    margin-right: 10px;
                }
            """)
            btn.setIcon(QIcon("asset/ui/fadeB.png"))

        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(35, 37, 42);
                    border: 1px solid rgba(255, 255, 255, 40);
                    border-radius: 6px;
                    padding: 3px;
                    margin-right: 10px;
                }
            """)
            btn.setIcon(QIcon("asset/ui/fade.png"))
    def handle_key(self, key):
        if key == Qt.Key.Key_1:
            fade_video = self.main_window.fade_background.isChecked()
            fade_slide = self.main_window.fade_slide.isChecked()

            # VIDEO FADE OUT
            if fade_video:
                self.video_anim = QPropertyAnimation(self.video_opacity, b"opacity")
                self.video_anim.setDuration(int(self.main_window.fade_background_time.value() * 1000))
                self.video_anim.setStartValue(1.0)
                self.video_anim.setEndValue(0.0)

                def video_finish():
                    self.video_enabled = False
                    self.video_label.clear()
                    self.video_label.hide()

                self.video_anim.finished.connect(video_finish)
                self.video_anim.start()
            else:
                self.video_enabled = False
                self.video_label.clear()
                self.video_label.hide()

            # SLIDE FADE OUT
            if fade_slide:
                self.fade_slide_out(self.main_window.fade_slide_time.value())
            else:
                self.slide_enabled = False
                self.slide_overlay.clear()
                self.slide_overlay.hide()

            self.update_layers()
            return

        elif key == Qt.Key.Key_2:
            if self.main_window.fade_background.isChecked():
                self.video_anim = QPropertyAnimation(self.video_opacity, b"opacity")
                self.video_anim.setDuration(int(self.main_window.fade_background_time.value() * 1000))
                self.video_anim.setStartValue(1.0)
                self.video_anim.setEndValue(0.0)

                def finish():
                    self.video_enabled = False
                    self.video_label.clear()
                    self.video_label.hide()

                self.video_anim.finished.connect(finish)
                self.video_anim.start()
            else:
                self.video_enabled = False
                self.update_layers()

        elif key == Qt.Key.Key_3:
            if self.main_window.fade_slide.isChecked():
                self.fade_slide_out(self.main_window.fade_slide_time.value())
            else:
                self.slide_enabled = False
                self.update_layers()

        self.update_layers()

    def fade_slide_in(self, duration):
        self.anim = QPropertyAnimation(self.slide_opacity, b"opacity")
        self.anim.setDuration(int(duration * 1000))
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
    def fade_slide_out(self, duration):
        self.anim = QPropertyAnimation(self.slide_opacity, b"opacity")
        self.anim.setDuration(int(duration * 1000))
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)

        def on_finish():
            self.slide_overlay.clear()
            self.slide_enabled = False

        self.anim.finished.connect(on_finish)
        self.anim.start()