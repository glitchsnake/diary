def get_stylesheet():
    return """
    QMainWindow, QDialog {
        background-color: #16171a;
        color: #f4f4f5;
    }
    
    QWidget {
        color: #e4e4e7;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Ubuntu, sans-serif;
        font-size: 13px;
    }

    QSplitter::handle {
        background-color: #26272b;
        width: 1px;
    }

    /* Frames */
    QFrame#sidebarFrame {
        background-color: #111215;
        border-right: 1px solid #232429;
    }

    QFrame#centerFrame {
        background-color: #16171a;
        border-right: 1px solid #232429;
    }

    QFrame#contentFrame {
        background-color: #16171a;
    }

    QFrame#statsBox {
        background-color: #1b1c21;
        border: 1px solid #282930;
        border-radius: 8px;
        padding: 10px;
    }

    /* Headings */
    QLabel#appTitle {
        font-size: 18px;
        font-weight: 700;
        color: #fafafa;
        letter-spacing: -0.5px;
    }

    QLabel#sectionHeader {
        font-size: 11px;
        font-weight: 700;
        color: #71717a;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 4px;
    }

    QLabel#statTitle {
        font-size: 11px;
        font-weight: 700;
        color: #a1a1aa;
        text-transform: uppercase;
    }

    QLabel#statItem {
        font-size: 12px;
        color: #d4d4d8;
    }

    /* Inputs */
    QLineEdit, QComboBox, QTextEdit {
        background-color: #1f2025;
        color: #fafafa;
        border: 1px solid #2e3038;
        border-radius: 6px;
        padding: 8px 10px;
        selection-background-color: #2563eb;
        selection-color: #ffffff;
    }

    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
        border: 1px solid #3b82f6;
    }

    QComboBox QAbstractItemView {
        background-color: #1f2025;
        color: #f4f4f5;
        border: 1px solid #2e3038;
        selection-background-color: #2563eb;
    }

    QTextEdit#editorText {
        background-color: #1b1c21;
        font-size: 15px;
        line-height: 1.6;
        padding: 14px;
        border-radius: 8px;
        border: 1px solid #282930;
    }

    QTextEdit#viewerText {
        background-color: transparent;
        border: none;
        font-size: 15px;
        line-height: 1.7;
        color: #e4e4e7;
    }

    /* Buttons */
    QPushButton {
        background-color: #23242a;
        color: #f4f4f5;
        border: 1px solid #32343d;
        border-radius: 6px;
        padding: 7px 14px;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #2c2e36;
        border-color: #434652;
    }

    QPushButton:pressed {
        background-color: #16171a;
    }

    QPushButton#btnPrimary {
        background-color: #2563eb;
        border: 1px solid #3b82f6;
        color: #ffffff;
        font-weight: 600;
        padding: 8px 14px;
    }

    QPushButton#btnPrimary:hover {
        background-color: #1d4ed8;
    }

    QPushButton#btnSecondarySmall {
        background-color: transparent;
        border: 1px dashed #3f3f46;
        color: #a1a1aa;
        font-size: 11px;
        padding: 4px 8px;
        border-radius: 4px;
    }

    QPushButton#btnSecondarySmall:hover {
        background-color: #23242a;
        color: #e4e4e7;
        border-color: #71717a;
    }

    QPushButton#btnDanger {
        background-color: transparent;
        color: #ef4444;
        border: 1px solid #7f1d1d;
    }

    QPushButton#btnDanger:hover {
        background-color: #7f1d1d;
        color: #fecaca;
    }

    /* Lists */
    QListWidget {
        background-color: transparent;
        border: none;
        outline: none;
    }

    QListWidget::item {
        border-radius: 6px;
        padding: 6px 10px;
        margin-bottom: 2px;
        color: #d4d4d8;
    }

    QListWidget::item:hover {
        background-color: #23242a;
    }

    QListWidget::item:selected {
        background-color: #2563eb;
        color: #ffffff;
    }

    /* Entries List Cards */
    QListWidget#entriesListWidget {
        background-color: transparent;
        border: none;
        padding: 2px;
    }

    QListWidget#entriesListWidget::item {
        background-color: #1b1c21;
        border: 1px solid #282930;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 6px;
    }

    QListWidget#entriesListWidget::item:hover {
        background-color: #22232a;
        border-color: #383a45;
    }

    QListWidget#entriesListWidget::item:selected {
        background-color: #1e293b;
        border: 1px solid #38bdf8;
    }

    /* Context Menus */
    QMenu {
        background-color: #1f2025;
        border: 1px solid #2e3038;
        border-radius: 6px;
        padding: 4px;
    }

    QMenu::item {
        padding: 6px 16px;
        border-radius: 4px;
        color: #e4e4e7;
    }

    QMenu::item:selected {
        background-color: #2563eb;
        color: #ffffff;
    }

    /* Scrollbars */
    QScrollBar:horizontal {
        height: 0px;
        width: 0px;
        background: transparent;
        border: none;
    }

    QScrollBar::handle:horizontal {
        height: 0px;
        background: transparent;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
        background: transparent;
    }

    QScrollBar:vertical {
        background: transparent;
        width: 6px;
        margin: 0;
    }

    QScrollBar::handle:vertical {
        background: #32343d;
        min-height: 20px;
        border-radius: 3px;
    }

    QScrollBar::handle:vertical:hover {
        background: #484b57;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    """
