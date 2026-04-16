from email.mime import base
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QColor, QFontMetrics, QPixmap
from PyQt6.QtCore import Qt

from elements import DraggableText, Elements, DraggableImage
from paths import resource_path
from paths import data_path
from PyQt6.QtGui import QPainterPath, QPen, QBrush
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtGui import QFont

TAG_LIST = [
    "Verse1", "Verse2", "Verse3", "Verse4",
    "PreChorus1", "PreChorus2",
    "Chorus1", "Chorus2",
    "Bridge",
    None
]
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

class Editor:
    THUMB_SIZE = (240, 140)
    def __init__(self, parent, lyrics_mode=False):

        
        self.parent = parent
        self.selected_slide = None
        self.lyrics_mode = lyrics_mode
        self.EnableLyricsMode(self.lyrics_mode)


        # DATA
        self.slides_data = []
        self.slide_thumbs = []
        self.slide_labels = []
        self.elements_manager = Elements(self)
        self.tag_index = 0

        # UI
        self.slidelabel = parent.editor_page.editingslide
        self.taglabel = parent.editor_page.taglabel
        self.preview = parent.editor_page.preview_slide
        self.slides = parent.editor_page.SlidesList
        self.elements = parent.editor_page.ElementsList

        # SCROLL CONTENT
        self.slides_container = QWidget()
        self.slides_layout = QVBoxLayout()
        self.slides_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.slides_container.setLayout(self.slides_layout)

        self.slides.setWidget(self.slides_container)
        self.slides.setWidgetResizable(True)

        self.slides_container.setStyleSheet("""
            #slide_row {
                background-color: transparent;
            }

            #slide_row[selected="true"] {
                background-color: rgba(100, 150, 255, 80);
                border: 2px solid rgb(100,150,255);
            }
            
            """)
        def preview_mouse_press(event):
            if self.elements_manager.selected_element:
                try:
                    if self.elements_manager.selected_element is not None:
                        self.elements_manager.selected_element.deselect()
                except RuntimeError:
                    pass  
                self.elements_manager.selected_element = None

        self.preview.mousePressEvent = preview_mouse_press

        self.center_icon = QLabel(self.preview)
        self.center_icon.setPixmap(QPixmap(resource_path("asset/ui/centerslide.png")))
        self.center_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.center_icon.setStyleSheet("background: transparent;")
        self.center_icon.hide()
        
        self.bg = QLabel(self.preview)
        self.bg.setScaledContents(True)
        self.bg.lower()
        self.bg.show()


        self.update_center_icon()
        self.apply_preview_style()
        self.preview.resizeEvent = self.on_preview_resize

    def EnableLyricsMode(self, enable):
        self.parent.editor_page.NewText.setEnabled(not enable)
        self.parent.editor_page.Upload.setEnabled(not enable)
        self.parent.editor_page.DeleteElement.setEnabled(not enable)
        self.parent.editor_page.ElementUp.setEnabled(not enable)
        self.parent.editor_page.ElementDown.setEnabled(not enable)


    def on_preview_resize(self, event):
        self.update_preview_background()
        self.update_center_icon()

    def save(self):
        if not hasattr(self, "current_show"):
            return

        lm = self.parent.lists_manager

        def clean_element(el):
            return {
                k: v for k, v in el.items()
                if k != "ref"
            }

        def clean_slide(slide):
            new_slide = {}

            for k, v in slide.items():
                if k == "elements":
                    new_slide["elements"] = [clean_element(e) for e in v]
                else:
                    new_slide[k] = v

            return new_slide

        def clean_show(show):
            new_show = show.copy()

            if "slides" in show:
                new_show["slides"] = [clean_slide(s) for s in show["slides"]]

            return new_show

        clean_playlists = []

        for pl in lm.playlists:
            new_pl = pl.copy()

            if "slides" in pl:
                new_pl["slides"] = [clean_show(s) for s in pl["slides"]]

            clean_playlists.append(new_pl)

        lm.json_manager.save(
            clean_playlists,
            lm.slides,
            lm.songs,
            lm.images
        )
    def load_show(self, show):
        self.current_show = show

        self.lyrics_mode = show.get("type") == "lyricsshow"
        self.EnableLyricsMode(self.lyrics_mode)

        if "slides" not in self.current_show:
            self.current_show["slides"] = []

        self.slides_data = self.current_show["slides"]

        self.selected_slide = None

        self.RenderSlides()
        self.RenderElements()
        self.RenderElementsList()
    
    def update_center_icon(self):
        if not self.center_icon or not self.center_icon.pixmap():
            return

        pix = self.center_icon.pixmap()

        w = pix.width()
        h = pix.height()

        pw = self.preview.width()
        ph = self.preview.height()

        x = (pw - w) // 2
        y = (ph - h) // 2

        self.center_icon.setGeometry(x, y, w, h)
    # -------------------------

    def select_slide(self, index):
        self.selected_slide = self.slides_data[index]
        self.slidelabel.setText(f"Editing Slide: {index + 1}")
        self.update_tag_label()
        self.RenderSlides()
        self.RenderElements()
        self.RenderElementsList()
        self.apply_preview_style()

    # -------------------------

    def add_slide(self):
        slide = {
            "thumbnail": resource_path("asset/ui/transparent.png"),
            "tag": None,
            "elements": []
        }

        if self.lyrics_mode:
            w, h = self.preview.width(), self.preview.height()
            text_element = {
                "type": "text",
                "text": "♪ Lyrics ♪",
                "x": int(w * 0.1),
                "y": int(h * 0.3),
                "w": int(w * 0.8),
                "h": int(h * 0.4)
            }
            slide["elements"].append(text_element)

        self.slides_data.append(slide)
        self.selected_slide = self.slides_data[-1]
        self.RenderSlides()
        self.RenderElements()
        self.RenderElementsList()
        self.save()
        self.apply_preview_style()

    # -------------------------

    def delete_slide(self):
        if self.selected_slide is None:
            return

        self.slides_data.remove(self.selected_slide)
        self.selected_slide = None
        self.RenderSlides()
        self.RenderElements()
        self.RenderElementsList()
        self.save()
        self.apply_preview_style()

    # -------------------------

    def move_slide(self, direction):
        if self.selected_slide is None:
            return

        index = self.slides_data.index(self.selected_slide)

        if direction == "up" and index > 0:
            self.slides_data[index], self.slides_data[index - 1] = \
                self.slides_data[index - 1], self.slides_data[index]

        elif direction == "down" and index < len(self.slides_data) - 1:
            self.slides_data[index], self.slides_data[index + 1] = \
                self.slides_data[index + 1], self.slides_data[index]

        self.RenderSlides()
        self.RenderElements()
        self.RenderElementsList()
        self.save()

    # -------------------------


    def generate_thumbnail(self, slide):
        SUPER_SCALE = 3
        thumb_w, thumb_h = self.THUMB_SIZE
        render_w, render_h = thumb_w * SUPER_SCALE, thumb_h * SUPER_SCALE

        full_pixmap = QPixmap(render_w, render_h)
        full_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(full_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        bg_pix = QPixmap(resource_path("asset/ui/transparent.png"))
        painter.drawPixmap(0, 0, render_w, render_h, bg_pix)

        if self.preview.width() > 0:
            total_scale_x = render_w / self.preview.width()
            total_scale_y = render_h / self.preview.height()
        else:
            total_scale_x = total_scale_y = SUPER_SCALE

        for el in slide.get("elements", []):

            x = int(el["x"] * total_scale_x)
            y = int(el["y"] * total_scale_y)
            w = int(el["w"] * total_scale_x)
            h = int(el["h"] * total_scale_y)

            if el["type"] == "text":
                text_str = el.get("text", "")

                font_size = max(16, int(32 * total_scale_y))
                font = QFont("Arial Black", font_size)
                font.setBold(True)
                font.setWeight(QFont.Weight.Black)

                painter.setFont(font)
                metrics = QFontMetrics(font)

                lines = text_str.split("\n")

                line_h = metrics.height()
                total_h = line_h * len(lines)

                start_y = y + (h - total_h) / 2 + metrics.ascent()

                for i, line in enumerate(lines):
                    if not line:
                        continue

                    tw = metrics.horizontalAdvance(line)

                    tx = int(x + (w - tw) / 2)
                    ty = int(start_y + i * line_h)


                    path = QPainterPath()
                    path.addText(tx, ty, font, line)

                    pen_w = max(2, int(3 * total_scale_y))
                    pen = QPen(
                        QColor(0, 0, 0),
                        pen_w,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin
                    )

                    painter.setPen(pen)
                    painter.setBrush(QColor(0, 0, 0))
                    painter.drawPath(path)


                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(255, 255, 255))
                    painter.drawPath(path)

            elif el["type"] == "image":
                img = QPixmap(data_path(el["path"]))
                if not img.isNull():
                    painter.drawPixmap(x, y, img.scaled(w, h, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation))

        painter.end()


        return full_pixmap.scaled(
            thumb_w, thumb_h, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )


    def update_slide_thumbnail(self, slide_index):
        if 0 <= slide_index < len(self.slide_thumbs):
            thumb_widget = self.slide_thumbs[slide_index]
            slide = self.slides_data[slide_index]
            thumb_widget.setPixmap(self.generate_thumbnail(slide).scaled(
                240, 140,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
    def on_element_changed(self):
        if self.selected_slide:
            slide_index = self.slides_data.index(self.selected_slide)
            self.update_slide_thumbnail(slide_index)
    def RenderSlides(self):
        for i in reversed(range(self.slides_layout.count())):
            widget = self.slides_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.slide_thumbs = []
        self.slide_labels = []  # Store label references

        for i, slide in enumerate(self.slides_data):
            row = QWidget()
            row.setObjectName("slide_row")

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(5, 5, 5, 5)
            row.setLayout(row_layout)

            thumb = QLabel()
            pixmap = self.generate_thumbnail(slide)
            thumb.setPixmap(
                pixmap.scaled(
                    240, 140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            thumb.setFixedSize(240, 140)
            row_layout.addWidget(thumb)
            self.slide_thumbs.append(thumb)  # Tallenna viittaus

            # tag ja label
            tag = slide.get("tag")
            r, g, b = self.get_tag_color(tag)
            thumb.setStyleSheet(f"""
                border: 4px solid rgb({r}, {g}, {b});
                border-radius: 6px;
            """)

            label = QLabel(f"{i + 1}")
            label.setStyleSheet("color: white; font-size: 16px;")
            row_layout.addWidget(label)
            row_layout.addStretch()
            self.slide_labels.append(label)  # Store label reference

            def make_click(idx):
                def handler(event):
                    self.select_slide(idx)
                return handler
            row.mousePressEvent = make_click(i)

            if slide is self.selected_slide:
                row.setProperty("selected", True)
                label.setStyleSheet("color: white; font-size: 16px; background-color: rgb(100, 150, 255); border-radius: 4px; padding: 4px;")
            else:
                row.setProperty("selected", False)
                label.setStyleSheet("color: white; font-size: 16px;")

            row.style().unpolish(row)
            row.style().polish(row)

            self.slides_layout.addWidget(row)

        self.apply_preview_style()

    # -------------------------

    def RenderElements(self):
        
        for child in self.preview.findChildren(QWidget):
            if hasattr(child, "data_ref"):
                child.deleteLater()
        if not self.selected_slide:
            return

        elements = self.selected_slide.get("elements", [])
        for data in elements:
            if data["type"] == "text":
                element = DraggableText(self.preview, self)

                element.setText(data["text"])
                element.setGeometry(data["x"], data["y"], data["w"], data["h"])

                element.data_ref = data
                data["ref"] = element

                element.show()
            elif data["type"] == "image":
                element = DraggableImage(self.preview, self)

                element.setGeometry(data["x"], data["y"], data["w"], data["h"])
                base = Path(__file__).resolve().parent
                pix = QPixmap(data_path(data["path"]))
                element.original_pixmap = pix
                element.update_pixmap()


                element.data_ref = data
                data["ref"] = element

                element.show()
        self.center_icon.show()
        self.update_center_icon()
    # -------------------------

    def new_text_element(self):
        if self.selected_slide:
            self.elements_manager.add_text_element(self.selected_slide)
            self.save()
    def new_image_element(self):
        if self.selected_slide:
            self.elements_manager.add_image_element(self.selected_slide)
            self.save()

    # -------------------------

    def rename_selected(self):
        if self.elements_manager.selected_element:
            self.elements_manager.rename_text_element(
                self.elements_manager.selected_element
            )
    def select_element(self, element):
        self.elements_manager.select_element(element)
        self.save()

    def delete_selected(self):
        self.elements_manager.delete_element()
        self.save()
    def move_selected_up(self):
        self.elements_manager.move_element("up")
        self.save()

    def move_selected_down(self):
        self.elements_manager.move_element("down")
        self.save()
    def CenterEvent(self):
        el = self.elements_manager.selected_element

        if not el:
            return

        pw = self.preview.width()
        ph = self.preview.height()

        w = el.width()
        h = el.height()

        x = (pw - w) // 2
        y = (ph - h) // 2

        el.setGeometry(x, y, w, h)
        if el.data_ref:
            el.data_ref["x"] = x
            el.data_ref["y"] = y
        self.save()

    def RenderElementsList(self):
        def short_text(txt):
            if not txt:
                return ""
            return txt if len(txt) <= 10 else txt[:10] + "..."
        def make_select(el_ref):
            def handler(event):
                if el_ref:
                    self.select_element(el_ref)
                    
            return handler
        container = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        container.setLayout(layout)

        self.elements.setWidget(container)
        self.elements.setWidgetResizable(True)

        

        if not self.selected_slide:
            return
        image_count = 0
        for el in self.selected_slide.get("elements", []):
            row = QWidget()
            row.mousePressEvent = make_select(el.get("ref"))
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(5, 5, 5, 5)
            row.setLayout(row_layout)

            icon = QLabel()
            icon_path = "asset/ui/textstyle.png" if el["type"] == "text" else "asset/ui/Image.png"
            icon.setPixmap(QPixmap(icon_path).scaled(24, 24))

            if el["type"] == "image":
                image_count += 1
                name = f"Image{image_count}"
            else:
                name = short_text(el.get("text", "Text"))
            text = QLabel(name)
            row_layout.addWidget(icon)
            row_layout.addWidget(text)
            row_layout.addStretch()

            layout.addWidget(row)
            if self.elements_manager.selected_element == el.get("ref"):
                row.setStyleSheet("background-color: rgba(100, 100, 255, 100);")
            else:
                row.setStyleSheet("")


    def update_preview_background(self):
        if not hasattr(self, "bg"):
            return

        pix = QPixmap(resource_path("asset/ui/transparent.png"))

        self.bg.setPixmap(pix)
        self.bg.setGeometry(
            0, 0,
            self.preview.width(),
            self.preview.height()
        )
        self.bg.raise_()
        self.bg.lower()
    def apply_preview_style(self):
        if not self.selected_slide:
            self.preview.setStyleSheet("")
            return

        tag = self.selected_slide.get("tag")
        r, g, b = self.get_tag_color(tag)

        self.preview.setObjectName("preview")
        self.preview.setStyleSheet(f"""
            QWidget#preview {{
                border: 6px solid rgb({r}, {g}, {b});
                background: transparent;
            }}
        """)

        self.update_preview_background()
    def get_tag_color(self, tag):
        return TAG_COLORS.get(tag, (150, 150, 150))
    
    
    def set_tag(self, tag):
        """Set the tag for the selected slide"""
        if not self.selected_slide:
            return

        self.selected_slide["tag"] = tag
        self.update_tag_label()
        self.RenderSlides()
        self.apply_preview_style()
        self.save()
    
    def update_tag_label(self):
        """Update the tag label to show the current slide's tag"""
        if not self.selected_slide:
            self.taglabel.setText("Tag: None")
            return
        
        tag = self.selected_slide.get("tag")
        tag_name = tag if tag else "None"
        self.taglabel.setText(f"Tag: {tag_name}")
        