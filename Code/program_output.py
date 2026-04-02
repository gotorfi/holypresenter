from PyQt6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation

class ProgramOutput:
    def __init__(self, show_manager):
        self.sm = show_manager
        self.outputs = []
        self.animations = []

    def add_output(self, frame: QWidget):
        # Current-labelit
        video_current = QLabel(frame)
        video_current.setGeometry(0, 0, frame.width(), frame.height())
        video_current.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        video_current.setStyleSheet("background:black;")
        video_current.show()

        slide_current = QLabel(frame)
        slide_current.setGeometry(0, 0, frame.width(), frame.height())
        slide_current.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        slide_current.setStyleSheet("background:transparent;")
        slide_current.show()

        # Next-labelit fadeä varten (vain yksi per output!)
        video_next = QLabel(frame)
        video_next.setGeometry(0, 0, frame.width(), frame.height())
        video_next.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        video_next.setStyleSheet("background:black;")
        video_next.hide()

        slide_next = QLabel(frame)
        slide_next.setGeometry(0, 0, frame.width(), frame.height())
        slide_next.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        slide_next.setStyleSheet("background:transparent;")
        slide_next.hide()

        # Opacity
        video_next_opacity = QGraphicsOpacityEffect()
        video_next.setGraphicsEffect(video_next_opacity)
        video_next_opacity.setOpacity(0.0)

        slide_next_opacity = QGraphicsOpacityEffect()
        slide_next.setGraphicsEffect(slide_next_opacity)
        slide_next_opacity.setOpacity(0.0)

        
        output = {
            "frame": frame,
            "video_current": video_current,
            "slide_current": slide_current,
            "video_next": video_next,
            "slide_next": slide_next,
            "video_next_opacity": video_next_opacity,
            "slide_next_opacity": slide_next_opacity,
            "video_fading": False,   # 🔹 Track if a fade is in progress
            "slide_fading": False
        }

        self.outputs.append(output)

        def resize_event(e):
            for lbl in [video_current, video_next, slide_current, slide_next]:
                lbl.setGeometry(0, 0, frame.width(), frame.height())
            return QWidget.resizeEvent(frame, e)

        frame.resizeEvent = resize_event

    def sync(self):
        if not hasattr(self.sm, "last_frame"):
            return

        for out in self.outputs:

            # ================= PROGRAM CONTROL =================
            # 🟥 UI pikkukuva (self.program)
            if hasattr(self.sm.main_window, "program"):
                if out["frame"] in [self.sm.main_window.program, self.sm.main_window.preview]:
                    if not self.sm.program_running:
                        out["video_current"].clear()
                        out["video_next"].clear()
                        out["slide_current"].clear()
                        out["slide_next"].clear()
                        continue

            # 🟥 Popup window
            if hasattr(self.sm.main_window, "program_window"):
                if out["frame"] == self.sm.main_window.program_window:
                    if not self.sm.program_running:
                        out["video_current"].clear()
                        out["video_next"].clear()
                        out["slide_current"].clear()
                        out["slide_next"].clear()
                        continue

            print("SYNC START",
                "video_enabled=", self.sm.video_enabled,
                "video_fading=", [out["video_fading"] for out in self.outputs],
                "has_last_frame=", self.sm.last_frame is not None
            )

            # ================= VIDEO =================
            if not self.sm.video_enabled and not out["video_fading"]:
                if not self.sm.last_frame:
                    out["video_current"].clear()
                    out["video_next"].clear()
            else:
                if self.sm.last_frame:
                    scaled_current = self.sm.last_frame.scaled(
                        out["frame"].width(),
                        out["frame"].height(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    out["video_current"].setPixmap(scaled_current)
                if not out["video_fading"] and self.sm.last_frame:
                    scaled_current = self.sm.last_frame.scaled(
                        out["frame"].width(),
                        out["frame"].height(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    out["video_current"].setPixmap(scaled_current)

                # 🔥 NEXT frame fade
                if out["video_fading"] and self.sm.last_next_frame:
                    scaled_next = self.sm.last_next_frame.scaled(
                        out["frame"].width(),
                        out["frame"].height(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    out["video_next"].setPixmap(scaled_next)

            # ================= SLIDE =================
            if not self.sm.slide_enabled:
                if not out["slide_fading"]:
                    out["slide_current"].clear()
                    out["slide_next"].clear()
            else:
                if self.sm.current_slide:

                    if out["frame"] in [self.sm.main_window.preview, self.sm.main_window.program]:
                        is_preview = True
                    else:
                        is_preview = False

                    pix = self.sm.render_slide_for_size(
                        self.sm.current_slide,
                        out["frame"].width(),
                        out["frame"].height(),
                        is_preview
                    )

                    if out["slide_fading"]:
                        out["slide_next"].setPixmap(pix)
                    else:
                        out["slide_current"].setPixmap(pix)

            # ================= LAYERS =================
            out["video_current"].lower()
            out["video_next"].lower()
            out["slide_current"].raise_()
            out["slide_next"].raise_()
    def fade_video(self, duration):

        for out in self.outputs:
            if out["video_fading"]:
                continue

            out["video_fading"] = True

            # ========================
            # NEXT näkyviin
            # ========================
            out["video_next"].show()
            out["video_next_opacity"].setOpacity(0.0)

            # ========================
            # CURRENT EFFECT (FIXED)
            # ========================
            current_effect = out["video_current"].graphicsEffect()

            if not isinstance(current_effect, QGraphicsOpacityEffect):
                current_effect = QGraphicsOpacityEffect()
                out["video_current"].setGraphicsEffect(current_effect)

            current_effect.setOpacity(1.0)

            # ========================
            # NEXT EFFECT
            # ========================
            next_effect = out["video_next_opacity"]

            # ========================
            # ANIMAATIOT
            # ========================
            anim_in = QPropertyAnimation(next_effect, b"opacity")
            anim_in.setDuration(int(duration * 1000))
            anim_in.setStartValue(0.0)
            anim_in.setEndValue(1.0)

            anim_out = QPropertyAnimation(current_effect, b"opacity")
            anim_out.setDuration(int(duration * 1000))
            anim_out.setStartValue(1.0)
            anim_out.setEndValue(0.0)

            def finish(o=out, ce=current_effect, ne=next_effect):
                if self.sm.last_next_frame:
                    self.sm.last_frame = self.sm.last_next_frame

                o["video_current"].setPixmap(o["video_next"].pixmap())

                o["video_next"].hide()

                # 🔥 TÄRKEIN FIX
                o["video_current"].setGraphicsEffect(None)

                # (vaihtoehtoisesti:)
                # ce.setOpacity(1.0)
                # mutta tämä ei aina riitä → siksi poistetaan effect kokonaan

                ne.setOpacity(0.0)

                o["video_fading"] = False

            anim_in.finished.connect(finish)

            self.animations.append(anim_in)
            self.animations.append(anim_out)

            anim_in.start()
            anim_out.start()
    def fade_slide(self, pixmap, duration):
        for out in self.outputs:

            out["slide_current"].clear()

            out["slide_fading"] = True

            out["slide_next"].setPixmap(pixmap)
            out["slide_next"].show()
            out["slide_next_opacity"].setOpacity(0.0)

            anim = QPropertyAnimation(out["slide_next_opacity"], b"opacity")
            anim.setDuration(int(duration * 1000))
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)

            def finish(o=out):
                o["slide_current"].setPixmap(o["slide_next"].pixmap())
                o["slide_next"].hide()
                o["slide_next_opacity"].setOpacity(0.0)
                o["slide_fading"] = False

            anim.finished.connect(finish)
            self.animations.append(anim)
            anim.start()

    def fade_video_out(self, duration):
        for out in self.outputs:
            anim = QPropertyAnimation(out["video_current"].graphicsEffect(), b"opacity")

            # jos ei ole efektiä, luodaan
            if not out["video_current"].graphicsEffect():
                effect = QGraphicsOpacityEffect()
                out["video_current"].setGraphicsEffect(effect)
                effect.setOpacity(1.0)
            else:
                effect = out["video_current"].graphicsEffect()

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(int(duration * 1000))
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)

            def finish(o=out, e=effect):
                o["video_current"].clear()
                e.setOpacity(1.0)

            anim.finished.connect(finish)
            self.animations.append(anim)
            anim.start()
    def fade_slide_out(self, duration):
        for out in self.outputs:

            effect = out["slide_current"].graphicsEffect()

            if not effect:
                effect = QGraphicsOpacityEffect()
                out["slide_current"].setGraphicsEffect(effect)
                effect.setOpacity(1.0)

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(int(duration * 1000))
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)

            def finish(o=out, e=effect):
                o["slide_current"].clear()
                e.setOpacity(1.0)
                o["slide_fading"] = False

            out["slide_fading"] = True
            anim.finished.connect(finish)
            self.animations.append(anim)
            anim.start()