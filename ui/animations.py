"""
J.A.R.V.I.S. -- Animations Module
Mark 50 (Infinity War) arc reactor widget and bootup animation.
"""

import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QRadialGradient, QBrush, QFont,
    QPolygonF,
)


class ArcReactorWidget(QWidget):
    """
    Mark 50 Infinity War arc reactor.
    Bright triangular core, concentric rings, gear-tooth segments,
    neon cyan-white glow radiating outward.
    """

    def __init__(self, parent=None, size=100):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Animation state
        self._pulse_phase = 0.0
        self._glow = 0.4
        self._is_active = False
        self._ring_rot = 0.0

        # ~33 fps
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def set_active(self, active: bool):
        self._is_active = active
        self.update()

    def _tick(self):
        self._ring_rot += (2.0 if self._is_active else 0.2)
        self._ring_rot %= 360

        self._pulse_phase += (0.10 if self._is_active else 0.03)
        if self._is_active:
            self._glow = 0.80 + 0.20 * math.sin(self._pulse_phase * 3)
        else:
            self._glow = 0.35 + 0.15 * math.sin(self._pulse_phase)
        self.update()

    # ── painting ─────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = self._size
        cx = s / 2
        cy = s / 2
        g = self._glow

        # ── 1. Outer neon bloom ──────────────────────
        bloom = QRadialGradient(cx, cy, s * 0.50)
        bloom.setColorAt(0.0, QColor(140, 230, 255, int(70 * g)))
        bloom.setColorAt(0.4, QColor(0, 180, 255, int(35 * g)))
        bloom.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bloom))
        p.drawEllipse(0, 0, s, s)

        # ── 2. Outer gear ring with teeth ────────────
        p.save()
        p.translate(cx, cy)
        p.rotate(self._ring_rot)

        outer_r = s * 0.40
        teeth = 16
        tw = max(3.0, s * 0.045)   # tooth width
        th = max(2.5, s * 0.040)   # tooth height

        # ring circle
        p.setPen(QPen(QColor(0, 200, 255, int(180 * g)), max(1.0, s * 0.015)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), outer_r, outer_r)

        # teeth
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(teeth):
            a = math.radians(i * (360 / teeth))
            tx = outer_r * math.cos(a)
            ty = outer_r * math.sin(a)
            p.save()
            p.translate(tx, ty)
            p.rotate(math.degrees(a))
            p.setBrush(QColor(0, 220, 255, int(210 * g)))
            p.drawRect(int(-tw / 2), int(-th / 2), int(tw), int(th))
            p.restore()

        p.restore()

        # ── 3. Dark gap (just leave empty space) ─────

        # ── 4. Inner bright ring ─────────────────────
        inner_r = s * 0.26
        p.setPen(QPen(QColor(100, 235, 255, int(200 * g)), max(1.0, s * 0.018)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        # ── 5. Triangular core (Mark 50) ─────────────
        tri_r = s * 0.15
        tri = QPolygonF()
        for i in range(3):
            a = math.radians(i * 120 - 90)
            tri.append(QPointF(cx + tri_r * math.cos(a),
                               cy + tri_r * math.sin(a)))

        # filled triangle glow
        p.setPen(QPen(QColor(180, 245, 255, int(255 * g)), max(1.0, s * 0.020)))
        p.setBrush(QColor(0, 200, 255, int(90 * g)))
        p.drawPolygon(tri)

        # ── 6. Core white-hot glow ───────────────────
        core_r = s * 0.09
        cg = QRadialGradient(cx, cy, core_r)
        cg.setColorAt(0.0, QColor(255, 255, 255, int(255 * g)))
        cg.setColorAt(0.35, QColor(200, 245, 255, int(230 * g)))
        cg.setColorAt(0.7, QColor(0, 200, 255, int(120 * g)))
        cg.setColorAt(1.0, QColor(0, 80, 180, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(cg))
        p.drawEllipse(QPointF(cx, cy), core_r, core_r)

        # center white dot
        dot_r = max(1.5, s * 0.025)
        dg = QRadialGradient(cx, cy, dot_r)
        dg.setColorAt(0, QColor(255, 255, 255, int(250 * g)))
        dg.setColorAt(1, QColor(180, 240, 255, int(80 * g)))
        p.setBrush(QBrush(dg))
        p.drawEllipse(QPointF(cx, cy), dot_r, dot_r)

        p.end()


# ═══════════════════════════════════════════════════
#  Bootup Overlay (unchanged from previous)
# ═══════════════════════════════════════════════════

class BootupOverlay(QWidget):
    """Full-screen bootup animation for 'Daddy's home' wake word."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0.0
        self._scan_line = 0
        self._boot_phase = 0
        self._boot_texts = [
            "INITIALIZING JARVIS PROTOCOL...",
            "LOADING NEURAL INTERFACE...",
            "ARC REACTOR ONLINE...",
            "SYSTEMS CHECK COMPLETE...",
            "ALL SYSTEMS NOMINAL.",
        ]
        self._current_text_idx = 0
        self._visible_chars = 0
        self._callback = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_boot)

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, val):
        self._opacity = val
        self.update()

    def start_bootup(self, callback=None):
        self._callback = callback
        self._opacity = 1.0
        self._scan_line = 0
        self._boot_phase = 0
        self._current_text_idx = 0
        self._visible_chars = 0
        self.show()
        self.raise_()
        self._timer.start(40)

    def _animate_boot(self):
        self._scan_line += 3
        if self._scan_line > self.height():
            self._scan_line = 0

        current_text = self._boot_texts[self._current_text_idx]
        if self._visible_chars < len(current_text):
            self._visible_chars += 1
        else:
            self._boot_phase += 1
            if self._boot_phase > 15:
                self._boot_phase = 0
                self._visible_chars = 0
                self._current_text_idx += 1
                if self._current_text_idx >= len(self._boot_texts):
                    self._timer.stop()
                    QTimer.singleShot(800, self._finish_boot)
        self.update()

    def _finish_boot(self):
        self.hide()
        if self._callback:
            self._callback()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        painter.fillRect(0, 0, w, h, QColor(5, 10, 20, int(240 * self._opacity)))

        # Scan line
        painter.setPen(QPen(QColor(0, 229, 255, 30), 1))
        painter.drawLine(0, self._scan_line, w, self._scan_line)

        # Grid
        painter.setPen(QPen(QColor(0, 100, 150, 15), 0.5))
        for x in range(0, w, 40):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, 40):
            painter.drawLine(0, y, w, y)

        # Boot text
        if self._current_text_idx < len(self._boot_texts):
            font = QFont("Consolas", 12)
            font.setBold(True)
            painter.setFont(font)
            y_start = h // 3
            for i in range(self._current_text_idx + 1):
                if i < self._current_text_idx:
                    painter.setPen(QColor(0, 180, 220, 120))
                    painter.drawText(60, y_start + i * 30, self._boot_texts[i])
                    painter.setPen(QColor(0, 255, 100, 150))
                    painter.drawText(40, y_start + i * 30, "v")
                elif i == self._current_text_idx:
                    visible = self._boot_texts[i][:self._visible_chars]
                    painter.setPen(QColor(0, 229, 255, 255))
                    painter.drawText(60, y_start + i * 30, visible)
                    if self._visible_chars < len(self._boot_texts[i]):
                        painter.setPen(QColor(0, 229, 255, 200))
                        cx = 60 + painter.fontMetrics().horizontalAdvance(visible)
                        painter.drawText(cx, y_start + i * 30, "|")
                    painter.setPen(QColor(0, 229, 255, 200))
                    painter.drawText(40, y_start + i * 30, ">")

        # Title
        title_font = QFont("Consolas", 24)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor(0, 229, 255, int(200 * self._opacity)))
        painter.drawText(0, 40, w, 50, Qt.AlignmentFlag.AlignCenter,
                         "J . A . R . V . I . S")

        sub_font = QFont("Consolas", 9)
        painter.setFont(sub_font)
        painter.setPen(QColor(0, 180, 220, int(120 * self._opacity)))
        painter.drawText(0, 70, w, 30, Qt.AlignmentFlag.AlignCenter,
                         "JUST A RATHER VERY INTELLIGENT SYSTEM")
        painter.end()
