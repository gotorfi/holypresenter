import cv2
from PyQt6.QtWidgets import QLabel, QSlider
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtCore import QObject, QTimer, Qt
from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QColor, QPen, QPainterPath
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation
from program_output import ProgramOutput

class ShowManager(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.preview_frame = main_window.preview  # QWidget, johon video näytetään

        self.program_output = ProgramOutput(self)
        self.video_label = QLabel(self.preview_frame)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.video_label.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.show()

        

        self.video_label_next = QLabel(self.preview_frame)
        self.video_label_next.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.video_label_next.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.video_label_next.hide()

        self.video_opacity = QGraphicsOpacityEffect()
        self.video_label_next.setGraphicsEffect(self.video_opacity)
        self.video_opacity.setOpacity(0.0)
        self.cap_next = None
        self.last_next_frame = None

        # SLIDE OVERLAY
        self.slide_overlay = QLabel(self.preview_frame)
        self.slide_overlay.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.slide_overlay.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.slide_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.slide_overlay.setStyleSheet("background: transparent;")
        self.slide_overlay.show()


        # 🔔 NOTIFICATION OVERLAY (TOP LAYER)
        self.notification_overlay = QLabel(self.preview_frame)
        self.notification_overlay.setGeometry(0, 0, self.preview_frame.width(), self.preview_frame.height())
        self.notification_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.notification_overlay.setStyleSheet("background: transparent;")
        self.notification_overlay.hide()


        self.slide_opacity = QGraphicsOpacityEffect()
        self.slide_overlay.setGraphicsEffect(self.slide_opacity)
        self.slide_opacity.setOpacity(1.0)
        
        self.video_current_opacity = QGraphicsOpacityEffect()
        self.video_label.setGraphicsEffect(self.video_current_opacity)
        self.video_current_opacity.setOpacity(1.0)

        # Slider ja videolength label main_window:sta
        self.slider: QSlider = main_window.videoslider
        self.length_label: QLabel = main_window.videolength
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider_pressed = False
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)

        self.video_current_opacity = QGraphicsOpacityEffect()
        self.video_label.setGraphicsEffect(self.video_current_opacity)
        self.video_current_opacity.setOpacity(1.0)


        self.preview_frame.installEventFilter(self)
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
        self.last_frame = None


        self.lyrics_enabled = False
        self.lyrics_position = "Down"
        self.lyrics_bg_color = "Green"

        self.program_running = False

        # 🔔 NOTIFICATION STATE
        self.notification_text = ""
        self.notification_visible = False
        self.notification_style_index = 0
    def update_lyrics_settings(self):
        pref = self.main_window.settings

        self.lyrics_enabled = pref.get("enable_lyrics", False)
        self.lyrics_position = pref.get("lyrics_position", "Down")
        self.lyrics_bg_color = pref.get("background_color", "Green")
        self.program_output.sync()
    def eventFilter(self, obj, event):
        if obj == self.preview_frame and event.type() == event.Type.Resize:
            self.handle_resize()
        return False
    def handle_resize(self):
        # Hanki nykyinen frame-koko
        w = self.preview_frame.width()
        h = self.preview_frame.height()

        # Päivitä geometria labelille
        self.video_label.setGeometry(0, 0, w, h)
        self.video_label_next.setGeometry(0, 0, w, h)
        self.slide_overlay.setGeometry(0, 0, w, h)
        self.notification_overlay.setGeometry(0, 0, w, h)

        # 🔹 PAKOTA VIDEO-PIXMAPI SKAALAUTUMAAN IKKUNAKOKOON
        if self.last_frame and self.video_enabled:
            scaled = self.last_frame.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_label.setPixmap(scaled)

        if self.last_next_frame and self.cap_next:
            scaled_next = self.last_next_frame.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_label_next.setPixmap(scaled_next)

        # 🔹 PAKOTA SLIDE-SKAALAUS
        if self.current_slide and self.slide_enabled:
            pix = self.render_slide_for_size(self.current_slide, w, h, True)
            self.slide_overlay.setPixmap(pix)

        # 🔹 PAKOTA ohjelman thumbnailien geometria
        for out in self.program_output.outputs:
            fw = out["frame"].width()
            fh = out["frame"].height()
            for lbl in [out["video_current"], out["video_next"], out["slide_current"], out["slide_next"]]:
                lbl.setGeometry(0, 0, fw, fh)
        # 🔹 SYNKRO PROGRAMOUTPUT
        self.program_output.sync()
        
    def on_resize(self, event):
        w = self.preview_frame.width()
        h = self.preview_frame.height()

        self.video_label.setGeometry(0, 0, w, h)
        self.video_label_next.setGeometry(0, 0, w, h)
        self.slide_overlay.setGeometry(0, 0, w, h)

        # 🔥 TÄRKEIN FIX: defer sync
        QTimer.singleShot(0, self.program_output.sync)

        return super(type(self.preview_frame), self.preview_frame).resizeEvent(event)

    def play_video(self, path):
        if not self.video_enabled:
            self.stop_video()
            self.cap = None
            self.cap_next = None
            self.last_next_frame = None
        fade_on = self.main_window.fade_background.isChecked()
        duration = self.main_window.fade_background_time.value()

        self.current_video_path = path
        self.video_enabled = True

        # =====================================
        # 🔥 FADE MODE (CROSSFADE)
        # =====================================
        if fade_on:
            # =====================================
            # 🔥 ENSIMMÄINEN VIDEO (fade from black)
            # =====================================
            if self.cap is None:
                self.cap = cv2.VideoCapture(path)

                if not self.cap.isOpened():
                    return

                ret, frame = self.cap.read()
                if not ret:
                    return

                self.current_frame_index = 0

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w

                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                qpix = QPixmap.fromImage(qimg)

                self.last_frame = qpix

                scaled = qpix.scaled(
                    self.preview_frame.width(),
                    self.preview_frame.height(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )

                self.video_label.setPixmap(scaled)
                self.video_label.show()
                self.video_enabled = True

                # 🔥 TÄRKEÄ
                self.program_output.sync()

                self.video_current_opacity.setOpacity(0.0)

                self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30

                self.slider.setMaximum(self.frame_count - 1)
                self.slider.setValue(0)

                self.timer.start(int(1000 / self.fps))

                self.video_anim = QPropertyAnimation(self.video_current_opacity, b"opacity")
                self.video_anim.setDuration(int(duration * 1000))
                self.video_anim.setStartValue(0.0)
                self.video_anim.setEndValue(1.0)
                self.video_anim.start()

                return

            # =====================================
            # 🔥 CROSSFADE VIDEO → VIDEO
            # =====================================
            if self.timer.isActive():
                self.timer.stop()

            self.cap_next = cv2.VideoCapture(path)

            if not self.cap_next.isOpened():
                print(f"Cannot open video {path}")
                return

            self.video_label_next.show()
            self.video_opacity.setOpacity(0.0)

            def update_next_frame():
                ret, frame = self.cap_next.read()
                if not ret:
                    self.cap_next.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    return

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w

                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pix = QPixmap.fromImage(qimg)

                scaled = pix.scaled(
                    self.preview_frame.width(),
                    self.preview_frame.height(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )

                self.video_label_next.setPixmap(scaled)

                # 🔥 TÄRKEIN FIX
                self.last_next_frame = pix
                self.program_output.sync()

                # 🔥 STARTAA FADE VASTA KUN FRAME ON OLEMASSA
                if self.last_next_frame and not hasattr(self, "_program_fade_started"):
                    self._program_fade_started = True
                    self.program_output.fade_video(duration)

            self.crossfade_timer = QTimer()
            self.crossfade_timer.timeout.connect(update_next_frame)
            self.crossfade_timer.start(int(1000 / self.fps))

            self.video_anim = QPropertyAnimation(self.video_opacity, b"opacity")
            self.video_anim.setDuration(int(duration * 1000))
            self.video_anim.setStartValue(0.0)
            self.video_anim.setEndValue(1.0)

            def finish():
                self.cap = self.cap_next
                self.cap_next = None

                if self.last_next_frame:
                    self.last_frame = self.last_next_frame

                self.video_label.setPixmap(self.video_label_next.pixmap())
                self.video_label_next.hide()
                self.video_opacity.setOpacity(0.0)

                if self.crossfade_timer:
                    self.crossfade_timer.stop()
                    self.crossfade_timer = None

                self.current_frame_index = 0

                self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30

                self.timer.start(int(1000 / self.fps))

                self.video_enabled = True
                self.video_label.show()
                self.video_current_opacity.setOpacity(1.0)

                # 🔥 TÄRKEIN: sync ennen kuin nollataan
                self.program_output.sync()


                if hasattr(self, "_program_fade_started"):
                    del self._program_fade_started

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
        qpix = QPixmap.fromImage(qimg)

        self.last_frame = qpix

        scaled = qpix.scaled(
            self.preview_frame.width(),
            self.preview_frame.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        self.video_label.setPixmap(scaled)
        self.program_output.sync()
        
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


        # 🔔 NOTIFICATION
        if self.notification_visible:
            pix = self.render_notification(
                self.preview_frame.width(),
                self.preview_frame.height()
            )
            self.notification_overlay.setPixmap(pix)
            self.notification_overlay.show()
            self.notification_overlay.raise_()
        else:
            self.notification_overlay.hide()
        self.program_output.sync()

        
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
            self.program_output.fade_slide(pix, duration)
        else:
            self.slide_opacity.setOpacity(1.0)
        self.program_output.sync()
        


    def render_notification(self, w, h):
        if not self.notification_text:
            return QPixmap()

        pix = QPixmap(w, h)
        pix.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        text = self.notification_text
        is_preview = w < 400

        if w < 300:
            BASE_W = 300
            BASE_H = 170
        else:
            BASE_W = 1450
            BASE_H = 825

        scale = min(w / BASE_W, h / BASE_H)


        if is_preview:
            styles = [
                ("top", 5),
                ("bottom", 5),
                ("center", 10),
                ("center", 20),
            ]
        else:
            styles = [
                ("top", 25),
                ("bottom", 25),
                ("center", 50),
                ("center", 100),
            ]
        

        pos, base_size = styles[self.notification_style_index]

        font_size = max(4, int(base_size))
        font = QFont("Arial Black", font_size)
        font.setBold(True)
        painter.setFont(font)

        metrics = QFontMetrics(font)

        rect = metrics.boundingRect(text)

        tw = rect.width()
        th = rect.height()

        margin = int(20 * scale)

        if pos == "top":
            x = int((w - tw) / 2)
            y = margin + th

        elif pos == "bottom":
            x = int((w - tw) / 2)
            y = h - margin

        else:  # center
            x = int((w - tw) / 2)
            y = int((h / 2) + (th / 2))

        path = QPainterPath()
        path.addText(x, y, font, text)

        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(max(2, int(6 * scale)))
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0))
        painter.drawPath(path)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPath(path)

        painter.end()
        return pix

    def render_slide(self, slide):
        w = self.preview_frame.width()
        h = self.preview_frame.height()

        BASE_W = 1450
        BASE_H = 825

        # 🔥 COVER SCALE (sama kuin video)
        scale = max(w / BASE_W, h / BASE_H)

        scaled_w = BASE_W * scale
        scaled_h = BASE_H * scale

        # 🔥 OFFSET (crop keskelle)
        offset_x = (w - scaled_w) / 2
        offset_y = (h - scaled_h) / 2

        pix = QPixmap(w, h)
        pix.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        for el in slide.get("elements", []):

            x = int(el["x"] * scale + offset_x)
            y = int(el["y"] * scale + offset_y)
            ww = int(el["w"] * scale)
            hh = int(el["h"] * scale)

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

                font_size = max(6, int(12 * scale))
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
                    ty = int(start_y + i * line_height)

                    path = QPainterPath()
                    path.addText(tx, ty, font, line)

                    pen = QPen(QColor(0, 0, 0))
                    pen.setWidth(max(4, int(6 * scale)))
                    painter.setPen(pen)
                    painter.setBrush(QColor(0, 0, 0))
                    painter.drawPath(path)

                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(255, 255, 255))
                    painter.drawPath(path)

        painter.end()
        return pix
    



    def render_slide_for_size(self, slide, w, h, is_preview=False):
        if slide is None:
            return QPixmap()

        BASE_W = 1450
        BASE_H = 825

        # 🔥 COVER SCALE (sama kuin video)
        scale = max(w / BASE_W, h / BASE_H)

        scaled_w = BASE_W * scale
        scaled_h = BASE_H * scale

        # 🔥 OFFSET (crop keskelle)
        offset_x = (w - scaled_w) / 2
        offset_y = (h - scaled_h) / 2

        pix = QPixmap(w, h)
        pix.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        for el in slide.get("elements", []):

            x = int(el["x"] * scale + offset_x)
            y = int(el["y"] * scale + offset_y)
            ww = int(el["w"] * scale)
            hh = int(el["h"] * scale)

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

                if is_preview:
                    font_size = max(6, int(12 * scale))
                else:
                    font_size = max(16, int(28 * scale))
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
                    ty = int(start_y + i * line_height)

                    path = QPainterPath()
                    path.addText(tx, ty, font, line)

                    pen = QPen(QColor(0, 0, 0))
                    if is_preview:
                        pen.setWidth(max(2, int(6 * scale)))
                    else:
                        pen.setWidth(max(6, int(12 * scale)))
                    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(pen)
                    painter.setBrush(QColor(0, 0, 0))
                    painter.drawPath(path)

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

        # =========================
        # KEY 1 — CLEAR ALL
        # =========================
        if key == Qt.Key.Key_1:

            fade_video = self.main_window.fade_background.isChecked()
            fade_slide = self.main_window.fade_slide.isChecked()

            # ========= VIDEO =========
            if fade_video:
                self.video_anim = QPropertyAnimation(self.video_current_opacity, b"opacity")
                self.video_anim.setDuration(int(self.main_window.fade_background_time.value() * 1000))
                self.video_anim.setStartValue(1.0)
                self.video_anim.setEndValue(0.0)

                def finish():
                    self.stop_video()
                    self.cap = None
                    self.cap_next = None

                    self.video_label.clear()
                    self.video_label.hide()

                    self.video_enabled = False
                    self.current_video_path = None

                    # reset vasta lopussa
                    self.video_current_opacity.setOpacity(1.0)
                    self.video_opacity.setOpacity(0.0)

                    self.program_output.sync()

                self.video_anim.finished.connect(finish)

                self.program_output.fade_video_out(self.main_window.fade_background_time.value())
                self.video_anim.start()

            else:
                self.stop_video()
                self.video_label.clear()
                self.video_label.hide()
                self.video_enabled = False
                self.current_video_path = None
                self.last_frame = None
                self.last_next_frame = None
                self.program_output.sync()

            # ========= SLIDE =========
            if fade_slide:
                self.fade_slide_out(self.main_window.fade_slide_time.value())
                self.program_output.fade_slide_out(self.main_window.fade_slide_time.value())
            else:
                self.slide_overlay.clear()
                self.slide_overlay.hide()
                self.slide_enabled = False
                self.current_slide = None

                self.program_output.sync()

            self.current_slide = None
            return

        # =========================
        # KEY 2 — VIDEO OFF
        # =========================
        elif key == Qt.Key.Key_2:
            fade_video = self.main_window.fade_background.isChecked()

            if fade_video:
                self.video_anim = QPropertyAnimation(self.video_current_opacity, b"opacity")
                self.video_anim.setDuration(int(self.main_window.fade_background_time.value() * 1000))
                self.video_anim.setStartValue(1.0)
                self.video_anim.setEndValue(0.0)

                def finish():
                    self.stop_video()
                    self.cap = None
                    self.cap_next = None

                    self.video_label.clear()
                    self.video_label.hide()

                    self.video_enabled = False
                    self.current_video_path = None

                    self.video_current_opacity.setOpacity(1.0)
                    self.video_opacity.setOpacity(0.0)

                    self.program_output.sync()

                self.video_anim.finished.connect(finish)

                self.program_output.fade_video_out(self.main_window.fade_background_time.value())
                self.video_anim.start()

            else:
                self.stop_video()
                self.video_label.clear()
                self.video_label.hide()
                self.video_enabled = False
                self.current_video_path = None
                self.last_frame = None
                self.last_next_frame = None
                self.program_output.sync()

            return

        # =========================
        # KEY 3 — SLIDE OFF
        # =========================
        elif key == Qt.Key.Key_3:
            if not self.current_slide:
                return
            fade_slide = self.main_window.fade_slide.isChecked()

            if fade_slide:
                self.fade_slide_out(self.main_window.fade_slide_time.value())
                self.program_output.fade_slide_out(self.main_window.fade_slide_time.value())
            else:
                self.slide_overlay.clear()
                self.slide_overlay.hide()
                self.slide_enabled = False
                self.current_slide = None

            self.current_slide = None
            return


        # fallback
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