from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from elements import DraggableText, Elements, DraggableImage


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
    "Chorus1": (255, 145, 195),
    "Chorus2": (255, 145, 195),
    "Bridge": (255, 183, 89),
    None: (150, 150, 150)
}

class Editor:
    def __init__(self, parent):

        
        self.parent = parent
        self.selected_slide = None


        # DATA
        self.slides_data = []
        self.elements_manager = Elements(self)
        self.tag_index = 0

        # UI
        self.slidelabel = parent.editor_page.editingslide
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
                self.elements_manager.selected_element.deselect()
                self.elements_manager.selected_element = None

        self.preview.mousePressEvent = preview_mouse_press

        self.center_icon = QLabel(self.preview)
        self.center_icon.setPixmap(QPixmap("asset/ui/centerslide.png"))
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

    def on_preview_resize(self, event):
        self.update_preview_background()
        self.update_center_icon()

    def save(self):
        if not hasattr(self, "current_show"):
            return

        self.current_show["slides"] = self.slides_data
        self.parent.lists_manager.save()
    def load_show(self, show):
        self.current_show = show

        if "slides" not in show:
            show["slides"] = []

        self.slides_data = show["slides"]

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
        print(f"Pressed slide: {index + 1}")
        self.slidelabel.setText(f"Editing Slide: {index + 1}")
        self.RenderSlides()
        self.RenderElements()
        self.RenderElementsList()
        self.apply_preview_style()

    # -------------------------

    def add_slide(self):
        slide = {
            "thumbnail": "asset/ui/transparent.png",
            "tag": None
        }
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

    def RenderSlides(self):
        for i in reversed(range(self.slides_layout.count())):
            widget = self.slides_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for i, slide in enumerate(self.slides_data):
            row = QWidget()
            row.setObjectName("slide_row")

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(5, 5, 5, 5)
            row.setLayout(row_layout)

            thumb = QLabel()
            pixmap = QPixmap(slide["thumbnail"])
            thumb.setPixmap(
                pixmap.scaled(
                    240, 140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            thumb.setFixedSize(240, 140)
            tag = slide.get("tag")
            r, g, b = self.get_tag_color(tag)

            thumb.setStyleSheet(f"""
                border: 4px solid rgb({r}, {g}, {b});
                border-radius: 6px;
            """)

            label = QLabel(f"{i + 1}")
            label.setStyleSheet("color: white; font-size: 16px;")


            def make_click(idx):
                def handler(event):
                    self.select_slide(idx)
                return handler

            row.mousePressEvent = make_click(i)

            if slide is self.selected_slide:
                row.setProperty("selected", True)
            else:
                row.setProperty("selected", False)

            row.style().unpolish(row)
            row.style().polish(row)

            row_layout.addWidget(thumb)
            row_layout.addWidget(label)
            row_layout.addStretch()

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
                pix = QPixmap(data["path"])
                element.original_pixmap = pix
                element.update_pixmap()


                element.data_ref = data
                data["ref"] = element

                element.show()
        self.center_icon.show()
        self.update_center_icon()
        self.save()
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
        self.save()


    def update_preview_background(self):
        if not hasattr(self, "bg"):
            return

        pix = QPixmap("asset/ui/transparent.png")

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
    def cycle_tag(self):
        if not self.selected_slide:
            return

        tags = TAG_LIST

        current = self.selected_slide.get("tag")
        if current not in tags:
            self.tag_index = 0
        else:
            self.tag_index = tags.index(current)

        self.tag_index = (self.tag_index + 1) % len(tags)
        new_tag = tags[self.tag_index]

        self.selected_slide["tag"] = new_tag

        self.RenderSlides()
        self.apply_preview_style()
        self.save()
        