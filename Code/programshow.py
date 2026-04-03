from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt



class ProgramShow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Program Output")
        self.resize(1280, 720)

    def resizeEvent(self, event):
        w = self.width()
        h = int(w * 9 / 16)

        if h > self.height():
            h = self.height()
            w = int(h * 16 / 9)

        self.resize(w, h)
        return super().resizeEvent(event)


class LyricsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lyrics Output")

    def resizeEvent(self, event):
        w = self.width()
        h = int(w * 9 / 16)

        if h > self.height():
            h = self.height()
            w = int(h * 16 / 9)

        self.resize(w, h)
        return super().resizeEvent(event)