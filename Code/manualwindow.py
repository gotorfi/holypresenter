from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtPdfWidgets import QPdfView

from PyQt6.QtPdf import QPdfDocument


class UserManualWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("User Manual")
        self.resize(800, 1000)

        # PDF document
        self.document = QPdfDocument(self)

        # Viewer
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        

        # Layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.pdf_view)
        container.setLayout(layout)

        self.setCentralWidget(container)
        self.load_pdf("asset/manual.pdf")

    def load_pdf(self, path):
        self.document.load(path)