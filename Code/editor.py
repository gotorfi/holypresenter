from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from elements import DraggableText, Elements, DraggableImage




class Editor:
    def __init__(self, parent):
        self.parent = parent
        self.selected_slide = None

        # DATA
        self.slides_data = []
        self.elements_manager = Elements(self)

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

        self.update_center_icon()


    
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

    # -------------------------

    def add_slide(self):
        slide = {
            "thumbnail": "asset/ui/transparent.png"
        }
        self.slides_data.append(slide)
        self.RenderSlides()
        self.RenderElements()
        self.RenderElementsList()

    # -------------------------

    def delete_slide(self):
        if self.selected_slide is None:
            return

        self.slides_data.remove(self.selected_slide)
        self.selected_slide = None
        self.RenderSlides()
        self.RenderElements()
        self.RenderElementsList()

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

    # -------------------------

    def RenderElements(self):
        
        for child in self.preview.children():
            if isinstance(child, (DraggableText, DraggableImage)):
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
    # -------------------------

    def new_text_element(self):
        if self.selected_slide:
            self.elements_manager.add_text_element(self.selected_slide)
    def new_image_element(self):
        if self.selected_slide:
            self.elements_manager.add_image_element(self.selected_slide)

    # -------------------------

    def rename_selected(self):
        if self.elements_manager.selected_element:
            self.elements_manager.rename_text_element(
                self.elements_manager.selected_element
            )
    def select_element(self, element):
        self.elements_manager.select_element(element)

    def delete_selected(self):
        self.elements_manager.delete_element()
    def move_selected_up(self):
        self.elements_manager.move_element("up")

    def move_selected_down(self):
        self.elements_manager.move_element("down")
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