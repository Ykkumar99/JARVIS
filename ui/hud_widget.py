"""
J.A.R.V.I.S. — HUD Widget
Main floating overlay with glassmorphism design.
Supports two modes: full HUD and compact arc reactor pill.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QApplication,
    QStackedWidget,
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QRect, QParallelAnimationGroup,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QLinearGradient, QBrush

from ui.animations import ArcReactorWidget, BootupOverlay
from ui.styles import MAIN_STYLESHEET
from config import HUD_WIDTH, HUD_HEIGHT, HUD_OPACITY, COMPACT_WIDTH, COMPACT_HEIGHT


class HudWidget(QWidget):
    """
    Floating always-on-top HUD overlay.
    Two modes:
      - FULL: Header, arc reactor, status, command, response, footer (420x320)
      - COMPACT: Pill with arc reactor + STANDBY label (200x200)
    Draggable in both modes. Remembers position across mode switches.
    """

    # Signals
    close_requested = pyqtSignal()
    minimize_requested = pyqtSignal()
    compact_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ── Mode state ───────────────────────────────
        self._is_compact = True
        self._animating = False

        # ── Position memory ──────────────────────────
        # Store the bottom-right anchor point. Both compact and full
        # modes are positioned so their bottom-right corner stays here.
        self._screen_geo = None
        screen = QApplication.primaryScreen()
        if screen:
            self._screen_geo = screen.availableGeometry()

        # Default anchor = bottom-right corner of screen with 20px margin
        if self._screen_geo:
            self._anchor_right = self._screen_geo.width() - 20
            self._anchor_bottom = self._screen_geo.height() - 20
        else:
            self._anchor_right = 1000
            self._anchor_bottom = 700

        self.setStyleSheet(MAIN_STYLESHEET)

        # ── Drag support ─────────────────────────────
        self._drag_pos = None
        self._was_dragging = False

        # ── Build UI ─────────────────────────────────
        self._build_ui()

        # ── Bootup overlay ───────────────────────────
        self._bootup = None

        # ── Keep animation references alive ──────────
        self._geo_anim = None
        self._opacity_anim = None
        self._anim_group = None

        # ── Start in compact mode ────────────────────
        self.setGeometry(self._compact_rect())
        self._stack.setCurrentIndex(0)

    def _compact_rect(self) -> QRect:
        """Geometry for compact mode, anchored to current position."""
        x = self._anchor_right - COMPACT_WIDTH
        y = self._anchor_bottom - COMPACT_HEIGHT
        return QRect(x, y, COMPACT_WIDTH, COMPACT_HEIGHT)

    def _full_rect(self) -> QRect:
        """Geometry for full mode, anchored to current position."""
        x = self._anchor_right - HUD_WIDTH
        y = self._anchor_bottom - HUD_HEIGHT
        return QRect(x, y, HUD_WIDTH, HUD_HEIGHT)

    def _update_anchor_from_geometry(self):
        """Update the anchor point from the current widget geometry."""
        geo = self.geometry()
        self._anchor_right = geo.x() + geo.width()
        self._anchor_bottom = geo.y() + geo.height()

    def _build_ui(self):
        """Build both compact and full UIs inside a QStackedWidget."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._stack = QStackedWidget()
        root_layout.addWidget(self._stack)

        # ── Page 0: Compact Mode ─────────────────────
        compact_page = QWidget()
        compact_page.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_compact(compact_page)
        self._stack.addWidget(compact_page)

        # ── Page 1: Full Mode ────────────────────────
        full_page = QWidget()
        full_page.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_full(full_page)
        self._stack.addWidget(full_page)

    def _build_compact(self, parent):
        """Build compact mode -- floating glowing reactor, no background."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Arc reactor -- 90px inside 140px widget (25px padding for glow bloom)
        self.compact_reactor = ArcReactorWidget(size=90)

        # Strong neon glow -- the main way users see this widget
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(40)
        glow.setColor(QColor(0, 200, 255, 200))
        glow.setOffset(0, 0)
        self.compact_reactor.setGraphicsEffect(glow)

        layout.addWidget(self.compact_reactor, alignment=Qt.AlignmentFlag.AlignCenter)

        # Nearly invisible STANDBY label
        self.compact_label = QLabel("STANDBY")
        self.compact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compact_label.setStyleSheet(
            "color: rgba(0, 200, 255, 0.25); font-size: 7px; font-weight: normal; letter-spacing: 2px;"
        )
        layout.addWidget(self.compact_label)

    def _build_full(self, parent):
        """Build the full HUD layout."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.frame = QFrame()
        self.frame.setObjectName("hudFrame")
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(16, 12, 16, 16)
        frame_layout.setSpacing(6)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 180, 255, 80))
        shadow.setOffset(0, 0)
        self.frame.setGraphicsEffect(shadow)

        # ── Header row ───────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(8)

        self.title_label = QLabel("J.A.R.V.I.S")
        self.title_label.setObjectName("titleLabel")
        header.addWidget(self.title_label)

        header.addStretch()

        self.minimize_btn = QPushButton("—")
        self.minimize_btn.setObjectName("minimizeBtn")
        self.minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minimize_btn.clicked.connect(self.minimize_requested.emit)
        header.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.close_requested.emit)
        header.addWidget(self.close_btn)

        frame_layout.addLayout(header)

        # ── Divider ──────────────────────────────────
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(0, 200, 255, 0.15);")
        frame_layout.addWidget(divider)

        # ── Center section: Arc Reactor + Status ─────
        center = QHBoxLayout()
        center.setSpacing(12)

        self.reactor = ArcReactorWidget(size=90)
        center.addWidget(self.reactor, alignment=Qt.AlignmentFlag.AlignCenter)

        status_col = QVBoxLayout()
        status_col.setSpacing(4)

        self.status_label = QLabel("● STANDBY")
        self.status_label.setObjectName("statusLabel")
        status_col.addWidget(self.status_label)

        self.command_label = QLabel("")
        self.command_label.setObjectName("commandLabel")
        self.command_label.setWordWrap(True)
        self.command_label.setMaximumHeight(30)
        status_col.addWidget(self.command_label)

        status_col.addStretch()
        center.addLayout(status_col, stretch=1)

        frame_layout.addLayout(center)

        # ── Divider ──────────────────────────────────
        divider2 = QFrame()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet("background-color: rgba(0, 200, 255, 0.1);")
        frame_layout.addWidget(divider2)

        # ── Response area ────────────────────────────
        self.response_label = QLabel("Awaiting activation...")
        self.response_label.setObjectName("responseLabel")
        self.response_label.setWordWrap(True)
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.response_label.setMinimumHeight(60)
        self.response_label.setMaximumHeight(100)
        frame_layout.addWidget(self.response_label)

        # ── Footer ───────────────────────────────────
        self.footer = QLabel("v1.0 - OFFLINE MODE")
        self.footer.setStyleSheet(
            "color: rgba(0, 200, 255, 0.3); font-size: 9px; letter-spacing: 1px; padding: 2px;"
        )
        self.footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.footer)

        layout.addWidget(self.frame)

    # ── Mode Queries ─────────────────────────────────

    def is_compact(self) -> bool:
        """Return whether HUD is currently in compact mode."""
        return self._is_compact

    # ── Cinematic Animations ─────────────────────────

    def expand_to_full(self, callback=None):
        """Animate from compact pill to full HUD -- holographic slide-up."""
        if not self._is_compact or self._animating:
            if callback:
                callback()
            return

        self._animating = True

        # Switch to full page BEFORE animation
        self._stack.setCurrentIndex(1)

        start_rect = self.geometry()
        end_rect = self._full_rect()

        self._geo_anim = QPropertyAnimation(self, b"geometry")
        self._geo_anim.setDuration(600)
        self._geo_anim.setStartValue(start_rect)
        self._geo_anim.setEndValue(end_rect)
        self._geo_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(600)
        self._opacity_anim.setStartValue(0.5)
        self._opacity_anim.setEndValue(HUD_OPACITY)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_group = QParallelAnimationGroup()
        self._anim_group.addAnimation(self._geo_anim)
        self._anim_group.addAnimation(self._opacity_anim)

        def _on_finished():
            self._is_compact = False
            self._animating = False
            if callback:
                callback()

        self._anim_group.finished.connect(_on_finished)
        self._anim_group.start()

    def shrink_to_compact(self, callback=None):
        """Animate from full HUD to compact pill -- slide down."""
        if self._is_compact or self._animating:
            if callback:
                callback()
            return

        self._animating = True

        # Update anchor from current position before shrinking
        self._update_anchor_from_geometry()

        start_rect = self.geometry()
        end_rect = self._compact_rect()

        self._geo_anim = QPropertyAnimation(self, b"geometry")
        self._geo_anim.setDuration(400)
        self._geo_anim.setStartValue(start_rect)
        self._geo_anim.setEndValue(end_rect)
        self._geo_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(400)
        self._opacity_anim.setStartValue(self.windowOpacity())
        self._opacity_anim.setEndValue(HUD_OPACITY)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self._anim_group = QParallelAnimationGroup()
        self._anim_group.addAnimation(self._geo_anim)
        self._anim_group.addAnimation(self._opacity_anim)

        def _on_finished():
            self._is_compact = True
            self._animating = False
            self._stack.setCurrentIndex(0)
            if callback:
                callback()

        self._anim_group.finished.connect(_on_finished)
        self._anim_group.start()

    # ── Legacy animation methods ─────────────────────

    def animate_in(self):
        """Fade in the HUD (starts in compact mode)."""
        self.setWindowOpacity(0)
        self.show()

        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(600)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(HUD_OPACITY)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._opacity_anim.start()

    def animate_out(self, callback=None):
        """Fade out the HUD."""
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(400)
        self._opacity_anim.setStartValue(self.windowOpacity())
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        if callback:
            self._opacity_anim.finished.connect(callback)
        self._opacity_anim.start()

    # ── Public API ───────────────────────────────────

    def set_state_standby(self):
        """Set HUD to standby mode."""
        self.status_label.setText("  STANDBY")
        self.status_label.setStyleSheet("color: rgba(0, 229, 255, 0.5);")
        self.reactor.set_active(False)
        self.compact_label.setText("STANDBY")
        self.compact_label.setStyleSheet(
            "color: rgba(0, 200, 255, 0.2); font-size: 7px; font-weight: normal; letter-spacing: 2px;"
        )
        self.compact_reactor.set_active(False)

    def set_state_listening(self):
        """Set HUD to active listening mode."""
        self.status_label.setText("  LISTENING")
        self.status_label.setStyleSheet("color: #00E5FF;")
        self.reactor.set_active(True)
        self.compact_label.setText("LISTENING")
        self.compact_label.setStyleSheet(
            "color: rgba(0, 229, 255, 0.3); font-size: 7px; font-weight: normal; letter-spacing: 2px;"
        )
        self.compact_reactor.set_active(True)

    def set_state_processing(self):
        """Set HUD to processing mode."""
        self.status_label.setText("  PROCESSING")
        self.status_label.setStyleSheet("color: #FFAB40;")

    def set_state_speaking(self):
        """Set HUD to speaking mode."""
        self.status_label.setText("  SPEAKING")
        self.status_label.setStyleSheet("color: #69F0AE;")

    def set_online_status(self, is_online: bool):
        """Update the footer to show ONLINE or OFFLINE."""
        if is_online:
            self.footer.setText("v1.0 - ONLINE")
            self.footer.setStyleSheet(
                "color: rgba(105, 240, 174, 0.6); font-size: 9px; letter-spacing: 1px; padding: 2px;"
            )
        else:
            self.footer.setText("v1.0 - OFFLINE MODE")
            self.footer.setStyleSheet(
                "color: rgba(0, 200, 255, 0.3); font-size: 9px; letter-spacing: 1px; padding: 2px;"
            )

    def set_command(self, text: str):
        """Display the user's command."""
        if len(text) > 80:
            text = text[:77] + "..."
        self.command_label.setText(f'"{text}"')

    def set_response(self, text: str):
        """Display JARVIS's response."""
        if len(text) > 200:
            text = text[:197] + "..."
        self.response_label.setText(text)

    def play_bootup(self, callback=None):
        """Play dramatic bootup animation (for 'Daddy's home')."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self._bootup = BootupOverlay()
            self._bootup.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            self._bootup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self._bootup.setGeometry(geo)
            self._bootup.start_bootup(callback=lambda: self._on_bootup_done(callback))

    def _on_bootup_done(self, callback=None):
        """Called when bootup animation finishes."""
        if self._bootup:
            self._bootup.close()
            self._bootup = None
        self.expand_to_full(callback=callback)

    # ── Drag Support (both modes) ────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._was_dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            self._was_dragging = True
            # Update anchor as we drag
            self._update_anchor_from_geometry()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # If it was a click (not a drag) on compact mode, emit signal
            if self._is_compact and not self._was_dragging and not self._animating:
                self.compact_clicked.emit()
            self._drag_pos = None
            self._was_dragging = False
        event.accept()

    def paintEvent(self, event):
        """Draw subtle outer glow."""
        super().paintEvent(event)
