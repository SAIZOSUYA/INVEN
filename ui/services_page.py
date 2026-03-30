from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.styles import APP_STYLESHEET


class ServiceDialog(QDialog):
    def __init__(self, parent=None, service_id: int | None = None):
        super().__init__(parent)
        self._sid = service_id
        self.setWindowTitle("Edit service" if service_id else "New service")
        self.setMinimumWidth(420)
        self.setStyleSheet(APP_STYLESHEET)

        self._code = QLineEdit()
        self._name = QLineEdit()
        self._price = QDoubleSpinBox()
        self._price.setMaximum(1e9)
        self._price.setDecimals(2)
        self._dur = QSpinBox()
        self._dur.setMaximum(99999)
        self._dur.setToolTip("0 = not specified")
        self._desc = QTextEdit()
        self._desc.setMaximumHeight(80)
        self._active = QCheckBox("Active")
        self._active.setChecked(True)

        form = QFormLayout()
        form.addRow("Code *", self._code)
        form.addRow("Name *", self._name)
        form.addRow("Price", self._price)
        form.addRow("Duration (min)", self._dur)
        form.addRow("Description", self._desc)
        form.addRow(self._active)

        if service_id:
            s = next((x for x in db.list_services("") if x["id"] == service_id), None)
            if s:
                self._code.setText(s["code"])
                self._name.setText(s["name"])
                self._price.setValue(float(s["price"]))
                self._dur.setValue(int(s["duration_minutes"] or 0))
                self._desc.setPlainText(s["description"] or "")
                self._active.setChecked(bool(s["is_active"]))

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(bb)

    def _save(self) -> None:
        if not self._code.text().strip() or not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Code and name are required.")
            return
        dur = self._dur.value() or None
        try:
            db.save_service(
                self._sid,
                self._code.text(),
                self._name.text(),
                self._price.value(),
                dur,
                self._desc.toPlainText(),
                1 if self._active.isChecked() else 0,
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class ServicesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_STYLESHEET)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search code or name…")
        self._search.returnPressed.connect(self.refresh)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["Code", "Name", "Price", "Duration (min)", "Active", "Description"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)

        btn_row = QHBoxLayout()
        add = QPushButton("Add service")
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
        t = QLabel("Services")
        t.setObjectName("pageTitle")
        sub = QLabel("Non-stock items: repairs, fees, and billable work.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addLayout(btn_row)
        lay.addWidget(self._table)

    def refresh(self) -> None:
        rows = db.list_services(self._search.text())
        self._table.setRowCount(0)
        for r in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            dur = r["duration_minutes"]
            vals = [
                r["code"],
                r["name"],
                f"{r['price']:.2f}",
                str(dur) if dur is not None else "",
                "Yes" if r["is_active"] else "No",
                (r["description"] or "")[:80],
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
        d = ServiceDialog(self, None)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit(self) -> None:
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, "Services", "Select a row.")
            return
        d = ServiceDialog(self, sid)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete(self) -> None:
        sid = self._selected_id()
        if sid is None:
            return
        if QMessageBox.question(self, "Confirm", "Delete this service?") != QMessageBox.StandardButton.Yes:
            return
        try:
            db.delete_service(sid)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
