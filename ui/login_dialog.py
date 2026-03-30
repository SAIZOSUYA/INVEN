from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from ui.styles import APP_STYLESHEET


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign in")
        self.setMinimumWidth(400)
        self.setStyleSheet(APP_STYLESHEET)

        title = QLabel("Welcome back")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("Sign in to your inventory workspace")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)

        self._user = QLineEdit()
        self._user.setPlaceholderText("Username")
        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw.setPlaceholderText("Password")

        form = QFormLayout()
        form.setSpacing(12)
        form.setContentsMargins(8, 16, 8, 8)
        form.addRow("Username", self._user)
        form.addRow("Password", self._pw)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        inner = QVBoxLayout()
        inner.setSpacing(4)
        inner.addWidget(title)
        inner.addWidget(sub)
        inner.addLayout(form)
        inner.addWidget(buttons)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setLayout(inner)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 36, 32, 36)
        root.addWidget(card)
