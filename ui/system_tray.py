"""
J.A.R.V.I.S. — System Tray Module
Manages the system tray icon and context menu.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QRadialGradient, QBrush
from PyQt6.QtCore import Qt


def create_tray_icon_pixmap() -> QPixmap:
    """Create a programmatic tray icon (arc reactor style)."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    cx, cy = size / 2, size / 2

    # Outer glow
    glow = QRadialGradient(cx, cy, size / 2)
    glow.setColorAt(0, QColor(0, 229, 255, 80))
    glow.setColorAt(1, QColor(0, 0, 0, 0))
    painter.setBrush(QBrush(glow))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)

    # Ring
    from PyQt6.QtGui import QPen
    painter.setPen(QPen(QColor(0, 200, 255, 200), 2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(8, 8, size - 16, size - 16)

    # Inner ring
    painter.setPen(QPen(QColor(0, 229, 255, 150), 1.5))
    painter.drawEllipse(16, 16, size - 32, size - 32)

    # Core
    core = QRadialGradient(cx, cy, 8)
    core.setColorAt(0, QColor(200, 240, 255, 255))
    core.setColorAt(1, QColor(0, 229, 255, 100))
    painter.setBrush(QBrush(core))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(int(cx - 8), int(cy - 8), 16, 16)

    painter.end()
    return pixmap


class JarvisTray:
    """System tray icon for JARVIS."""

    def __init__(self, parent_widget, on_show=None, on_quit=None):
        self.tray = QSystemTrayIcon(parent_widget)
        self.tray.setIcon(QIcon(create_tray_icon_pixmap()))
        self.tray.setToolTip("J.A.R.V.I.S. — AI Assistant")

        # Context menu
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(10, 15, 30, 240);
                color: #E0F7FA;
                border: 1px solid rgba(0, 200, 255, 0.3);
                padding: 4px;
                font-family: 'Segoe UI';
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(0, 200, 255, 0.15);
            }
        """)

        show_action = QAction("Show JARVIS", parent_widget)
        if on_show:
            show_action.triggered.connect(on_show)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("Quit", parent_widget)
        if on_quit:
            quit_action.triggered.connect(on_quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

        # Double click to show
        if on_show:
            self.tray.activated.connect(
                lambda reason: on_show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
            )

    def show(self):
        self.tray.show()

    def hide(self):
        self.tray.hide()

    def show_message(self, title: str, message: str):
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
