from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.styles import APP_STYLESHEET


class CustomerDialog(QDialog):
    def __init__(self, parent=None, cid: int | None = None):
        super().__init__(parent)
        self._cid = cid
        self.setWindowTitle("Edit customer" if cid else "New customer")
        self.setMinimumWidth(400)
        self.setStyleSheet(APP_STYLESHEET)
        self._name = QLineEdit()
        self._phone = QLineEdit()
        self._email = QLineEdit()
        self._addr = QTextEdit()
        self._addr.setMaximumHeight(60)
        self._notes = QTextEdit()
        self._notes.setMaximumHeight(60)
        form = QFormLayout()
        form.addRow("Name *", self._name)
        form.addRow("Phone", self._phone)
        form.addRow("Email", self._email)
        form.addRow("Address", self._addr)
        form.addRow("Notes", self._notes)
        if cid:
            for r in db.list_customers(""):
                if r["id"] == cid:
                    self._name.setText(r["name"])
                    self._phone.setText(r["phone"] or "")
                    self._email.setText(r["email"] or "")
                    self._addr.setPlainText(r["address"] or "")
                    self._notes.setPlainText(r["notes"] or "")
                    break
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(bb)

    def _save(self) -> None:
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        try:
            db.save_customer(
                self._cid,
                self._name.text(),
                self._phone.text(),
                self._email.text(),
                self._addr.toPlainText(),
                self._notes.toPlainText(),
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class CustomersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_STYLESHEET)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search name or phone…")
        self._search.returnPressed.connect(self.refresh)
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Name", "Phone", "Email", "Address", "Notes"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        btn_row = QHBoxLayout()
        add = QPushButton("Add")
        add.clicked.connect(self._add)
        edit = QPushButton("Edit")
        edit.clicked.connect(self._edit)
        del_ = QPushButton("Delete")
        del_.setObjectName("danger")
        del_.clicked.connect(self._delete)
        srch = QPushButton("Search")
        srch.clicked.connect(self.refresh)
        btn_row.addWidget(add)
        btn_row.addWidget(edit)
        btn_row.addWidget(del_)
        btn_row.addStretch()
        btn_row.addWidget(self._search)
        btn_row.addWidget(srch)
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel("Customers")
        t.setObjectName("pageTitle")
        sub = QLabel("People and businesses you sell to.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addLayout(btn_row)
        lay.addWidget(self._table)

    def refresh(self) -> None:
        rows = db.list_customers(self._search.text())
        self._table.setRowCount(0)
        for r in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            vals = [r["name"], r["phone"] or "", r["email"] or "", r["address"] or "", (r["notes"] or "")[:60]]
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
        d = CustomerDialog(self, None)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit(self) -> None:
        cid = self._selected_id()
        if cid is None:
            QMessageBox.information(self, "Customers", "Select a row.")
            return
        d = CustomerDialog(self, cid)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete(self) -> None:
        cid = self._selected_id()
        if cid is None:
            return
        if QMessageBox.question(self, "Confirm", "Delete this customer?") != QMessageBox.StandardButton.Yes:
            return
        try:
            db.delete_customer(cid)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
