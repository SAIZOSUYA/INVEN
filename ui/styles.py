"""Application stylesheet — warm neutrals + teal accent."""

APP_STYLESHEET = """
/* ---- Base ---- */
QMainWindow, QDialog {
    background-color: #fafaf9;
    font-size: 13px;
    color: #1c1917;
    font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
}
QWidget {
    color: #1c1917;
}
QFrame#contentShell {
    background-color: #fafaf9;
}
QFrame#loginCard {
    background-color: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 16px;
    padding: 8px;
}

/* ---- Sidebar (dark) ---- */
QFrame#sidePanel {
    background-color: #1c1917;
    border: none;
}
QLabel#brandTitle {
    font-size: 20px;
    font-weight: 700;
    color: #fafaf9;
    letter-spacing: -0.5px;
}
QLabel#brandTagline {
    font-size: 11px;
    color: #a8a29e;
    font-weight: 400;
    padding-bottom: 8px;
}
QLabel#navSection {
    font-size: 10px;
    font-weight: 700;
    color: #78716c;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: 16px 4px 8px 4px;
}
QListWidget#navList {
    background: transparent;
    color: #e7e5e4;
    border: none;
    padding: 4px 0;
    font-size: 13px;
    outline: none;
}
QListWidget#navList::item {
    padding: 11px 14px;
    border-radius: 8px;
    margin: 2px 0;
    color: #d6d3d1;
}
QListWidget#navList::item:hover {
    background-color: #292524;
    color: #fafaf9;
}
QListWidget#navList::item:selected {
    background-color: #0d9488;
    color: #ffffff;
    font-weight: 600;
}
QListWidget#navList::item:selected:hover {
    background-color: #0f7668;
    color: #ffffff;
}
QPushButton#logoutBtn {
    background-color: transparent;
    color: #a8a29e;
    border: 1px solid #44403c;
    border-radius: 8px;
    padding: 10px 14px;
    font-weight: 500;
}
QPushButton#logoutBtn:hover {
    background-color: #292524;
    color: #fafaf9;
    border-color: #57534e;
}

/* ---- Page chrome ---- */
QLabel#pageTitle, QLabel#title {
    font-size: 26px;
    font-weight: 700;
    color: #1c1917;
    letter-spacing: -0.6px;
}
QLabel#pageSubtitle {
    font-size: 13px;
    color: #78716c;
    padding-bottom: 4px;
}
QLabel#title {
    font-size: 26px;
    font-weight: 700;
    color: #1c1917;
    letter-spacing: -0.6px;
}
QLabel#subtitle {
    font-size: 13px;
    color: #78716c;
}
QLabel#stat {
    font-size: 30px;
    font-weight: 700;
    color: #0f7668;
    letter-spacing: -0.5px;
}
QLabel#statLabel {
    font-size: 12px;
    color: #78716c;
    font-weight: 500;
}

/* ---- Cards & groups ---- */
QGroupBox {
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #e7e5e4;
    border-radius: 12px;
    margin-top: 14px;
    padding: 20px 16px 16px 16px;
    background-color: #ffffff;
    color: #44403c;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #57534e;
}

/* ---- Buttons ---- */
QPushButton {
    background-color: #0d9488;
    color: #ffffff;
    border: none;
    padding: 10px 18px;
    border-radius: 9px;
    min-height: 20px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #0f7668;
}
QPushButton:pressed {
    background-color: #115e59;
}
QPushButton#secondary {
    background-color: #f5f5f4;
    color: #44403c;
    border: 1px solid #d6d3d1;
}
QPushButton#secondary:hover {
    background-color: #e7e5e4;
    border-color: #a8a29e;
}
QPushButton#danger {
    background-color: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
}
QPushButton#danger:hover {
    background-color: #fee2e2;
    border-color: #f87171;
}

/* ---- Inputs ---- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
    padding: 9px 12px;
    border: 1px solid #d6d3d1;
    border-radius: 9px;
    background-color: #ffffff;
    color: #1c1917;
    selection-background-color: #99f6e4;
    selection-color: #134e4a;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
    border-color: #0d9488;
    outline: none;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1c1917;
    border: 1px solid #e7e5e4;
    border-radius: 8px;
    selection-background-color: #ccfbf1;
    selection-color: #134e4a;
    padding: 4px;
}

/* ---- Tables ---- */
QTableWidget {
    gridline-color: #f5f5f4;
    background-color: #ffffff;
    alternate-background-color: #fafaf9;
    border: 1px solid #e7e5e4;
    border-radius: 12px;
    color: #1c1917;
}
QTableWidget::item {
    color: #1c1917;
    padding: 6px 4px;
}
QTableWidget::item:selected {
    background-color: #ccfbf1;
    color: #134e4a;
}
QHeaderView::section {
    background-color: #fafaf9;
    padding: 10px 8px;
    border: none;
    border-bottom: 1px solid #e7e5e4;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #78716c;
}

/* ---- Dialog buttons (OK/Cancel) ---- */
QDialogButtonBox QPushButton {
    min-width: 88px;
    padding: 9px 16px;
}

/* ---- Scrollbars ---- */
QScrollBar:vertical {
    background: #f5f5f4;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #d6d3d1;
    border-radius: 5px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #a8a29e;
}
QScrollBar:horizontal {
    background: #f5f5f4;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #d6d3d1;
    border-radius: 5px;
    min-width: 28px;
}

QLabel {
    color: #1c1917;
}
"""
