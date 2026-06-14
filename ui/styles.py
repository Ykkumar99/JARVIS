"""
J.A.R.V.I.S. — QSS Styles
Dark glassmorphism theme with cyan/blue glow.
"""

MAIN_STYLESHEET = """
/* ─── Global ─────────────────────────────────── */
QWidget {
    font-family: 'Segoe UI', 'Consolas', monospace;
    color: #E0F7FA;
}

/* ─── Main HUD Frame ─────────────────────────── */
QFrame#hudFrame {
    background-color: rgba(10, 15, 30, 230);
    border: 1px solid rgba(0, 200, 255, 0.3);
    border-radius: 16px;
}

/* ─── Status Label ───────────────────────────── */
QLabel#statusLabel {
    color: #00E5FF;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 4px 8px;
}

/* ─── Command Display ────────────────────────── */
QLabel#commandLabel {
    color: rgba(176, 190, 197, 0.9);
    font-size: 11px;
    padding: 2px 12px;
    font-style: italic;
}

/* ─── Response Display ───────────────────────── */
QLabel#responseLabel {
    color: #E0F7FA;
    font-size: 12px;
    padding: 4px 12px;
    line-height: 1.4;
}

/* ─── Title Label ────────────────────────────── */
QLabel#titleLabel {
    color: #00E5FF;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 4px;
}

/* ─── Minimize Button ────────────────────────── */
QPushButton#minimizeBtn {
    background-color: transparent;
    border: 1px solid rgba(0, 200, 255, 0.3);
    border-radius: 10px;
    color: #00E5FF;
    font-size: 14px;
    padding: 2px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
}
QPushButton#minimizeBtn:hover {
    background-color: rgba(0, 200, 255, 0.15);
    border-color: rgba(0, 200, 255, 0.6);
}

/* ─── Close Button ───────────────────────────── */
QPushButton#closeBtn {
    background-color: transparent;
    border: 1px solid rgba(255, 80, 80, 0.3);
    border-radius: 10px;
    color: #FF5252;
    font-size: 12px;
    font-weight: bold;
    padding: 2px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
}
QPushButton#closeBtn:hover {
    background-color: rgba(255, 80, 80, 0.15);
    border-color: rgba(255, 80, 80, 0.6);
}

/* ─── Scrollbar ──────────────────────────────── */
QScrollBar:vertical {
    width: 4px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: rgba(0, 200, 255, 0.3);
    border-radius: 2px;
}

/* ─── Compact Mode Frame ────────────────────── */
QFrame#compactFrame {
    background-color: rgba(8, 12, 25, 240);
    border: 1px solid rgba(0, 200, 255, 0.4);
    border-radius: 65px;
}

/* ─── Compact Standby Label ─────────────────── */
QLabel#compactLabel {
    color: rgba(0, 200, 255, 0.35);
    font-size: 8px;
    font-weight: normal;
    letter-spacing: 3px;
}
"""
