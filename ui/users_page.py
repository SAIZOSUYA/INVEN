from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.styles import APP_STYLESHEET


class UserDialog(QDialog):
    def __init__(self, parent=None, uid: int | None = None, current_username: str = ""):
        super().__init__(parent)
        self._uid = uid
        self.setWindowTitle("Edit user" if uid else "New user")
        self.setMinimumWidth(380)
        self.setStyleSheet(APP_STYLESHEET)

        self._user = QLineEdit()
        self._user.setEnabled(uid is None)
        self._full = QLineEdit()
        self._role = QComboBox()
        self._role.addItem("Admin", "admin")
        self._role.addItem("Staff", "staff")
        self._active = QCheckBox("Active")
        self._active.setChecked(True)
        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw.setPlaceholderText("Required for new user" if not uid else "Leave blank to keep")

        form = QFormLayout()
        form.addRow("Username *", self._user)
        form.addRow("Full name", self._full)
        form.addRow("Role", self._role)
        form.addRow(self._active)
        form.addRow("Password", self._pw)

        if uid:
            for r in db.list_users():
                if r["id"] == uid:
                    self._user.setText(r["username"])
                    self._full.setText(r["full_name"] or "")
                    idx = self._role.findData(r["role"])
                    if idx >= 0:
                        self._role.setCurrentIndex(idx)
                    self._active.setChecked(bool(r["is_active"]))
                    if r["username"] == current_username:
                        self._role.setEnabled(False)
                        self._active.setEnabled(False)
                    break

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(bb)

    def _save(self) -> None:
        if not self._uid and (not self._user.text().strip() or not self._pw.text()):
            QMessageBox.warning(self, "Users", "Username and password are required.")
            return
        try:
            if not self._uid:
                db.create_user(
                    self._user.text(),
                    self._pw.text(),
                    self._full.text(),
                    self._role.currentData(),
                )
            else:
                db.update_user(
                    self._uid,
                    self._full.text(),
                    self._role.currentData(),
                    1 if self._active.isChecked() else 0,
                )
                if self._pw.text().strip():
                    db.set_user_password(self._uid, self._pw.text())
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class UsersPage(QWidget):
    def __init__(self, parent=None, current_user: dict | None = None):
        super().__init__(parent)
        self._me = current_user or {}
        self.setStyleSheet(APP_STYLESHEET)
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Username", "Full name", "Role", "Active", "Created"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)

        btn = QHBoxLayout()
        add = QPushButton("Add user")
        add.clicked.connect(self._add)
        edit = QPushButton("Edit")
        edit.clicked.connect(self._edit)
        btn.addWidget(add)
        btn.addWidget(edit)
        btn.addStretch()

        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel("Users")
        t.setObjectName("pageTitle")
        sub = QLabel("Who can sign in and what they are allowed to do.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addLayout(btn)
        lay.addWidget(self._table)

    def refresh(self) -> None:
        rows = db.list_users()
        self._table.setRowCount(0)
        for r in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            vals = [
                r["username"],
                r["full_name"] or "",
                r["role"],
                "Yes" if r["is_active"] else "No",
                (r["created_at"] or "")[:19],
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setData(Qt.ItemDataRole.UserRole, r["id"])
                self._table.setItem(row, c, it)

    def _selected_id(self) -> int | None:
        items = self._table.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)

    def _add(self) -> None:
        d = UserDialog(self, None, self._me.get("username", ""))
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit(self) -> None:
        uid = self._selected_id()
        if uid is None:
            QMessageBox.information(self, "Users", "Select a user.")
            return
        d = UserDialog(self, uid, self._me.get("username", ""))
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
