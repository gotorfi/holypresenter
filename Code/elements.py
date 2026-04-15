from pathlib import Path

from PyQt6.QtWidgets import QLabel, QLineEdit
from PyQt6.QtCore import QPointF, Qt, QPoint, QRect
from PyQt6.QtGui import QMouseEvent, QPen, QPixmap

from paths import resource_path, data_path



from PyQt6.QtWidgets import QLabel, QLineEdit
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QMouseEvent, QPainter, QColor, QFont
from PyQt6.QtWidgets import QTextEdit

import os
import shutil
from PyQt6.QtWidgets import QFileDialog


BASE_DIR = Path(__file__).resolve().parent

def resource_path(rel):
    return str(BASE_DIR / rel)


class MultiLineTextEdit(QTextEdit):
    def __init__(self, parent=None, finish_callback=None):
        super().__init__(parent)
        self.finish_callback = finish_callback
    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text())

    def keyPressEvent(self, event):
        # ENTER ilman shift = hyväksy
        if event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            if self.finish_callback:
                self.finish_callback()
        else:
            super().keyPressEvent(event)
            




class DraggableImage(QLabel):
    def __init__(self, parent, editor):
        super().__init__(parent)
        self.editor = editor
        self.selected = False


        self.handle_size = 24
        self.resizing = False
        self.dragging = False
        self.offset = QPoint()
        self.start_mouse_pos = None
        self.start_size = None
        self.original_pixmap = None

        self.handle = QLabel(self)
        self.handle.setFixedSize(self.handle_size, self.handle_size)
        self.handle.setPixmap(
            QPixmap(resource_path("asset/ui/drag.png")).scaled(
                self.handle_size, self.handle_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        self.handle.setStyleSheet("background: transparent; border: none;")
        self.handle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.handle.hide()
        self.update_handle_position()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        
    def update_pixmap(self):
        if not self.original_pixmap:
            return

        scaled = self.original_pixmap.scaled(
            self.width(),
            self.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
    def select(self):
        self.selected = True
        self.handle.show()
        self.handle.raise_()
        self.update()

    def deselect(self):
        self.selected = False
        self.handle.hide()
        self.update()

    def resizeEvent(self, event):
        self.update_handle_position()
        self.update_pixmap()


    def snap_to_center(self):
        parent = self.parent()
        if not parent:
            return

        center_x = parent.width() // 2
        center_y = parent.height() // 2

        my_center_x = self.x() + self.width() // 2
        my_center_y = self.y() + self.height() // 2

        threshold = 15

        if abs(my_center_x - center_x) < threshold:
            self.move(center_x - self.width() // 2, self.y())

        if abs(my_center_y - center_y) < threshold:
            self.move(self.x(), center_y - self.height() // 2)
    def mousePressEvent(self, event):
        
        self.editor.select_element(self)

        if event.button() != Qt.MouseButton.LeftButton:
            return
        
        self.dragging = False
        self.resizing = False
        if self.is_on_resize_corner(event.pos()):
            self.resizing = True
            self.start_mouse_pos = event.globalPosition().toPoint()
            self.start_size = self.size()
        else:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.MouseButton.LeftButton:
            return

        if self.resizing:
            delta = event.globalPosition().toPoint() - self.start_mouse_pos
            new_w = max(50, self.start_size.width() + delta.x())
            new_h = max(50, self.start_size.height() + delta.y())

            parent_rect = self.parent().rect()
            new_w = min(new_w, parent_rect.width() - self.x())
            new_h = min(new_h, parent_rect.height() - self.y())

            self.resize(new_w, new_h)
            if self.selected:
                self.handle.raise_()

        elif self.dragging:
            new_pos = self.mapToParent(event.pos() - self.offset)

            parent_rect = self.parent().rect()
            x = max(0, min(new_pos.x(), parent_rect.width() - self.width()))
            y = max(0, min(new_pos.y(), parent_rect.height() - self.height()))

            self.move(x, y)
            self.snap_to_center()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.save()

    def is_on_resize_corner(self, pos):
        return pos.x() > self.width()-20 and pos.y() > self.height()-20

    def save(self):
        el = self.data_ref
        el["x"] = self.x()
        el["y"] = self.y()
        el["w"] = self.width()
        el["h"] = self.height()
    def update_handle_position(self):
        self.handle.move(
            self.width() - self.handle_size,
            self.height() - self.handle_size
        )
        self.handle.raise_()
    def resizeEvent(self, event):
        self.update_handle_position()
        self.update_pixmap()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.selected:
            painter = QPainter(self)
            pen = QPen(QColor("#66ccff"))
            pen.setWidth(4)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.rect().adjusted(2, 2, -2, -2))

class DraggableText(QLabel):
    def __init__(self, parent, editor):
        super().__init__(parent)
        self.data_ref = None
        self.editor = editor
        self.setObjectName("text_element")
        
        self.text_content = "New Text"
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Fontti
        self.font_size = 36
        self.setFont(QFont("Arial", self.font_size, QFont.Weight.Bold))

        self.setGeometry(50, 50, 300, 120)

        # Drag/resize tilat
        self.dragging = False
        self.resizing = False
        self.offset = QPoint()
        self.start_mouse_pos = None
        self.start_size = None
        
        # Cache the drag handle pixmap - use absolute path this time
        base_dir = Path(__file__).resolve().parent.parent
        drag_icon_path = base_dir / "asset" / "ui" / "drag.png"
        self.drag_pixmap = QPixmap(str(drag_icon_path)).scaled(
            24, 24,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.handle = QLabel(self)
        self.handle_size = 24
        self.handle.setPixmap(
            QPixmap(resource_path("asset/ui/drag.png")).scaled(
                self.handle_size, self.handle_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        self.setWordWrap(True)
        self.handle.setFixedSize(self.handle_size, self.handle_size)
        self.handle.setMouseTracking(True)
        self.handle.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        # Remove transparent for mouse events - we want it visible!
        self.handle.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.handle.setStyleSheet("background: transparent; border: none; margin: 0px; padding: 0px;")
        self.handle.hide()

        self.selected = False
        self.update_handle_position()
        self.handle.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

    # -------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.TextAntialiasing
        )

        rect = self.rect()
        flags = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap

        
        painter.setPen(QColor(0, 0, 0))
        stroke_size = 8

        for dx in range(-stroke_size, stroke_size + 1):
            for dy in range(-stroke_size, stroke_size + 1):
                if dx == 0 and dy == 0:
                    continue
                painter.drawText(rect.adjusted(dx, dy, dx, dy), flags, self.text_content)

        painter.setPen(QColor(255,255,255))
        painter.drawText(rect, flags, self.text_content)

        if self.selected:
            pen = QPen(QColor("#66ccff"))
            pen.setWidth(5)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(2, 2, -2, -2))
            
            # Draw the cached drag handle in the bottom-right corner
            if not self.drag_pixmap.isNull():
                handle_x = self.width() - self.handle_size - 4
                handle_y = self.height() - self.handle_size - 4
                painter.drawPixmap(handle_x, handle_y, self.drag_pixmap)

    # -------------------------
    def setText(self, text: str):
        self.text_content = text
        self.update()
        
    def text(self):
        return self.text_content

    # -------------------------
    def select(self):
        self.selected = True
        self.raise_()
        self.setStyleSheet("""
            border: 5px solid #66ccff;
            background: transparent;
        """)
        self.update()  # Trigger paint event to show the drag handle

    def deselect(self):
        self.selected = False
        self.setStyleSheet("""
            border: none;
            background: transparent;
        """)
        self.update()  # Trigger paint event to hide the drag handle

    # -------------------------

    def snap_to_center(self):
        parent = self.parent()
        if not parent:
            return

        center_x = parent.width() // 2
        center_y = parent.height() // 2

        my_center_x = self.x() + self.width() // 2
        my_center_y = self.y() + self.height() // 2

        threshold = 15

        if abs(my_center_x - center_x) < threshold:
            self.move(center_x - self.width() // 2, self.y())

        if abs(my_center_y - center_y) < threshold:
            self.move(self.x(), center_y - self.height() // 2)

    def update_handle_position(self):
        # Position handle in bottom-right corner, outside the text area
        handle_x = self.width() - self.handle_size - 4
        handle_y = self.height() - self.handle_size - 4
        self.handle.move(handle_x, handle_y)
        self.handle.raise_()
        self.handle.setGeometry(handle_x, handle_y, self.handle_size, self.handle_size)

    def is_on_resize_corner(self, pos):
        margin = self.handle_size
        return pos.x() >= self.width() - margin and pos.y() >= self.height() - margin

    # -------------------------
    # Drag/resize
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self.editor.select_element(self)

        if self.is_on_resize_corner(event.pos()):
            self.resizing = True
            self.start_mouse_pos = event.globalPosition().toPoint()
            self.start_size = self.size()
            self.dragging = False
        else:
            self.dragging = True
            self.offset = event.pos()
            self.resizing = False

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() != Qt.MouseButton.LeftButton:
            return

        if self.resizing:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.start_mouse_pos
            new_width = max(50, self.start_size.width() + delta.x())
            new_height = max(30, self.start_size.height() + delta.y())
            parent_rect = self.parent().rect()
            new_width = min(new_width, parent_rect.width() - self.x())
            new_height = min(new_height, parent_rect.height() - self.y())
            self.resize(new_width, new_height)
            if self.selected:
                self.handle.raise_()
            return

        if self.dragging:
            new_pos = self.mapToParent(event.pos() - self.offset)
            parent_rect = self.parent().rect()
            x = max(0, min(new_pos.x(), parent_rect.width() - self.width()))
            y = max(0, min(new_pos.y(), parent_rect.height() - self.height()))
            self.move(x, y)
            self.snap_to_center()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        self.resizing = False
        self.save_to_slide()

    def resizeEvent(self, event):
        self.update_handle_position()

    def save_to_slide(self):
        slide = self.editor.selected_slide
        if not slide:
            return
        for el in slide.get("elements", []):
            if el.get("ref") == self:
                el["x"] = self.x()
                el["y"] = self.y()
                el["w"] = self.width()
                el["h"] = self.height()
                el["text"] = self.text()

class Elements:
    def __init__(self, parent):
        self.parent = parent
        self.selected_element = None

    # -------------------------


    def get_image_folder(self):
        base = Path(__file__).resolve().parent / "savecloud" / "slideimages"
        base.mkdir(parents=True, exist_ok=True)
        return base
    def add_image_element(self, slide):
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent.parent,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )

        if not file_path:
            return

        folder = Path(self.get_image_folder())
        filename = Path(file_path).name
        target_path = folder / filename

        project_root = Path(__file__).resolve().parent
        relative_path = target_path.relative_to(project_root)

        if not target_path.exists():
            shutil.copy(file_path, target_path)

        preview = self.parent.preview
        center_x = preview.width() // 2 - 100
        center_y = preview.height() // 2 - 100

        element_data = {
            "type": "image",
            "path": str(relative_path).replace("\\", "/"),
            "x": center_x,
            "y": center_y,
            "w": 200,
            "h": 200
        }

        if "elements" not in slide:
            slide["elements"] = []

        slide["elements"].append(element_data)

        self.parent.RenderElements()
        self.parent.RenderElementsList()
        self.parent.on_element_changed()

    def add_text_element(self, slide):
        preview = self.parent.preview
        center_x = preview.width() // 2 - 150
        center_y = preview.height() // 2 - 60

        element_data = {
            "type": "text",
            "text": "New Text",
            "x": center_x,
            "y": center_y,
            "w": 300,
            "h": 120
        }

        if "elements" not in slide:
            slide["elements"] = []

        slide["elements"].append(element_data)
        self.parent.RenderElements()
        self.parent.RenderElementsList()

        last = slide["elements"][-1]
        ref = last.get("ref")

        if ref:
            self.select_element(ref)
        self.parent.on_element_changed()

    # -------------------------

    def select_element(self, element):
        if self.selected_element:
            try:
                self.selected_element.deselect()
            except RuntimeError:
                pass

        self.selected_element = element
        element.select()
        self.parent.RenderElementsList()
    # -------------------------

    def delete_element(self):
        if not self.selected_element:
            return

        element = self.selected_element

        slide = self.parent.selected_slide
        if slide:
            slide["elements"] = [
                el for el in slide.get("elements", [])
                if el.get("ref") != element
            ]

        try:
            element.deleteLater()
        except:
            pass

        self.selected_element = None

        self.parent.RenderElements()
        self.parent.RenderElementsList()
        self.parent.on_element_changed()

    # -------------------------

    def rename_text_element(self, element: DraggableText):
        # Hide the original element while editing
        element.hide()
        
        def finish():
            text = editor.toPlainText().strip() or "Empty"
            element.setText(text)

            if hasattr(element, "data_ref") and element.data_ref is not None:
                element.data_ref["text"] = text

            editor.deleteLater()
            element.show()
            element.update()
            self.parent.RenderElementsList()
            self.parent.on_element_changed()
            self.parent.save()

        def update_padding():
            """Recalculate and apply padding to center text vertically"""
            fm = editor.fontMetrics()
            text_height = fm.height()
            lines = editor.toPlainText().count("\n") + 1
            total_text_height = text_height * lines
            padding = max(0, (editor.height() - total_text_height) // 2)
            
            editor.setStyleSheet(f"""
                background: rgba(100, 100, 255, 51);
                color: white;
                font-weight: bold;
                padding-top: {padding}px;
            """)

        editor = MultiLineTextEdit(element.parent(), finish_callback=finish)
        editor.setPlainText(element.text())
        editor.setGeometry(element.x(), element.y(), element.width(), element.height())
        editor.setFont(element.font())

        # Connect to text changed to recalculate padding dynamically
        editor.textChanged.connect(update_padding)

        # Set all text blocks to center alignment
        def center_all_blocks():
            cursor = editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            fmt = QTextBlockFormat()
            fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cursor.mergeBlockCharFormat(QTextCharFormat())
            cursor.clearSelection()
            
            # Alternative: iterate through blocks
            block = editor.document().firstBlock()
            while block.isValid():
                cursor.setPosition(block.position())
                fmt = QTextBlockFormat()
                fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cursor.setBlockFormat(fmt)
                block = block.next()

        # Import QTextCursor and QTextBlockFormat if not already imported
        from PyQt6.QtGui import QTextCursor, QTextBlockFormat, QTextCharFormat
        
        center_all_blocks()

        # Initial padding calculation
        update_padding()

        editor.show()
        editor.setFocus()

        def on_focus_out(event):
            finish()
            QTextEdit.focusOutEvent(editor, event)

        editor.focusOutEvent = on_focus_out

    def move_element(self, direction):
        if not self.selected_element:
            return

        slide = self.parent.selected_slide
        if not slide:
            return

        elements = slide.get("elements", [])

        index = None
        for i, el in enumerate(elements):
            if el.get("ref") == self.selected_element:
                index = i
                break

        if index is None:
            return

        if direction == "up" and index < len(elements) - 1:
            elements[index], elements[index + 1] = elements[index + 1], elements[index]

        elif direction == "down" and index > 0:
            elements[index], elements[index - 1] = elements[index - 1], elements[index]

        self.parent.RenderElements()
        self.parent.RenderElementsList()
        self.parent.on_element_changed()



    def center_element(self):
        if not self.selected_element:
            return

        parent = self.selected_element.parent()
        if not parent:
            return

        new_x = parent.width() // 2 - self.selected_element.width() // 2
        new_y = parent.height() // 2 - self.selected_element.height() // 2

        self.selected_element.move(new_x, new_y)

        self.parent.RenderElements()
        self.parent.RenderElementsList()
        self.selected_element.save()
        self.parent.on_element_changed()