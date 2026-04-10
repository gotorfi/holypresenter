from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTextBrowser
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
try:
    from PyQt6.QtPdfWidgets import QPdfView
    from PyQt6.QtPdf import QPdfDocument
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from paths import resource_path


class UserManualWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("User Manual")
        self.resize(800, 1000)

        container = QWidget()
        layout = QVBoxLayout(container)

        if PDF_AVAILABLE:
            self.document = QPdfDocument(self)
            self.pdf_view = QPdfView(self)
            self.pdf_view.setDocument(self.document)
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            self.pdf_view.setPageNavigationMode(QPdfView.PageNavigationMode.ScrollPerPage)
            layout.addWidget(self.pdf_view)
            self.load_pdf(resource_path("manual.pdf"))
        else:
            self.text_view = QTextBrowser(self)
            self.text_view.setOpenExternalLinks(True)
            pdf_path = resource_path("manual.pdf")
            self.text_view.setHtml(
                "<h2>User Manual</h2>"
                "<p>PDF support is unavailable in this PyQt6 build.</p>"
                f"<p><a href=\"{QUrl.fromLocalFile(pdf_path).toString()}\">Open the manual PDF</a></p>"
                "<p>Install QtPdf support or use a newer Qt/PyQt version for built-in PDF viewing.</p>"
            )
            layout.addWidget(self.text_view)

        self.setCentralWidget(container)

    def load_pdf(self, path):
        if PDF_AVAILABLE:
            self.document.load(path)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))