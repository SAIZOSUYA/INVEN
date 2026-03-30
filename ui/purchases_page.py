from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.styles import APP_STYLESHEET


class PurchaseViewDialog(QDialog):
    def __init__(self, parent=None, purchase_id: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Purchase details")
        self.setMinimumSize(560, 400)
        self.setStyleSheet(APP_STYLESHEET)
        p, items = db.get_purchase(purchase_id)
        assert p is not None
        info = QLabel(
            f"<b>{p['reference_no']}</b> &nbsp; Date: {p['purchase_date']} &nbsp; "
            f"Supplier: {p['supplier_name'] or '—'} &nbsp; Buyer: {p['buyer']}<br>"
            f"Subtotal: {p['subtotal']:.2f} &nbsp; <b>Total: {p['total']:.2f}</b>"
        )
        info.setWordWrap(True)
        tbl = QTableWidget(0, 5)
        tbl.setHorizontalHeaderLabels(["SKU", "Product", "Qty", "Unit cost", "Line total"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for it in items:
            row = tbl.rowCount()
            tbl.insertRow(row)
            tbl.setItem(row, 0, QTableWidgetItem(it["sku"]))
            tbl.setItem(row, 1, QTableWidgetItem(it["product_name"]))
            tbl.setItem(row, 2, QTableWidgetItem(str(it["qty"])))
            tbl.setItem(row, 3, QTableWidgetItem(f"{it['unit_cost']:.2f}"))
            tbl.setItem(row, 4, QTableWidgetItem(f"{it['line_total']:.2f}"))
        notes = QLabel(p["notes"] or "")
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        lay = QVBoxLayout(self)
        lay.addWidget(info)
        lay.addWidget(tbl)
        if p["notes"]:
            lay.addWidget(QLabel("<b>Notes</b>"))
            lay.addWidget(notes)
        lay.addWidget(close_btn)


class PurchaseDialog(QDialog):
    def __init__(self, parent=None, user_id: int = 1):
        super().__init__(parent)
        self._user_id = user_id
        self.setWindowTitle("New purchase (stock in)")
        self.setMinimumSize(680, 440)
        self.setStyleSheet(APP_STYLESHEET)

        self._sup = QComboBox()
        self._sup.addItem("None", None)
        for s in db.list_suppliers(""):
            self._sup.addItem(s["name"], s["id"])

        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDate(QDate.currentDate())
        self._date.setDisplayFormat("yyyy-MM-dd")

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(60)

        self._products = {r["id"]: r for r in db.list_products("")}

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Product", "Qty", "Unit cost", "Line"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        head = QHBoxLayout()
        add_line = QPushButton("+ Line")
        add_line.clicked.connect(self._add_row)
        rm_line = QPushButton("− Line")
        rm_line.setObjectName("danger")
        rm_line.clicked.connect(self._remove_row)
        head.addWidget(add_line)
        head.addWidget(rm_line)
        head.addStretch()

        form = QGridLayout()
        form.addWidget(QLabel("Supplier"), 0, 0)
        form.addWidget(self._sup, 0, 1)
        form.addWidget(QLabel("Date"), 0, 2)
        form.addWidget(self._date, 0, 3)
        form.addWidget(QLabel("Notes"), 1, 0)
        form.addWidget(self._notes, 1, 1, 1, 3)

        self._tot_lbl = QLabel("Total: 0.00")
        self._tot_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #0f7668; letter-spacing: -0.3px;"
        )

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addLayout(head)
        lay.addWidget(self._table)
        lay.addWidget(self._tot_lbl)
        lay.addWidget(bb)

        self._add_row()

    def _add_row(self) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        icb = QComboBox()
        for pid, p in sorted(self._products.items(), key=lambda x: x[1]["name"].lower()):
            icb.addItem(f"{p['sku']} — {p['name']}", pid)
        q = QDoubleSpinBox()
        q.setMaximum(1e9)
        q.setDecimals(3)
        q.setValue(1.0)
        c = QDoubleSpinBox()
        c.setMaximum(1e9)
        c.setDecimals(2)
        lt = QLabel("0.00")
        self._table.setCellWidget(row, 0, icb)
        self._table.setCellWidget(row, 1, q)
        self._table.setCellWidget(row, 2, c)
        self._table.setCellWidget(row, 3, lt)
        q.valueChanged.connect(self._recalc)
        c.valueChanged.connect(self._recalc)

        def on_item():
            pid = icb.currentData()
            if pid in self._products:
                c.setValue(float(self._products[pid]["cost_price"]))
            self._recalc()

        try:
            icb.currentIndexChanged.disconnect()
        except TypeError:
            pass
        icb.currentIndexChanged.connect(on_item)
        on_item()
        self._recalc()

    def _remove_row(self) -> None:
        r = self._table.currentRow()
        if r < 0:
            return
        self._table.removeRow(r)
        self._recalc()

    def _recalc(self) -> None:
        sub = 0.0
        for r in range(self._table.rowCount()):
            q = self._table.cellWidget(r, 1)
            c = self._table.cellWidget(r, 2)
            lt = self._table.cellWidget(r, 3)
            if not isinstance(q, QDoubleSpinBox) or not isinstance(c, QDoubleSpinBox) or not isinstance(lt, QLabel):
                continue
            line = round(q.value() * c.value(), 2)
            lt.setText(f"{line:.2f}")
            sub += line
        self._tot_lbl.setText(f"Total: {sub:.2f}")

    def _save(self) -> None:
        lines: list[dict] = []
        for r in range(self._table.rowCount()):
            icb = self._table.cellWidget(r, 0)
            q = self._table.cellWidget(r, 1)
            c = self._table.cellWidget(r, 2)
            if not isinstance(icb, QComboBox) or not isinstance(q, QDoubleSpinBox) or not isinstance(c, QDoubleSpinBox):
                continue
            pid = icb.currentData()
            if pid is None:
                continue
            lines.append({"product_id": int(pid), "qty": q.value(), "unit_cost": c.value()})
        if not lines:
            QMessageBox.warning(self, "Purchase", "Add at least one product line.")
            return
        try:
            db.create_purchase(
                self._user_id,
                self._sup.currentData(),
                self._date.date().toString("yyyy-MM-dd"),
                self._notes.toPlainText(),
                lines,
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Purchase failed", str(e))


class PurchasesPage(QWidget):
    def __init__(self, parent=None, user_id: int = 1):
        super().__init__(parent)
        self._user_id = user_id
        self.setStyleSheet(APP_STYLESHEET)
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["Reference", "Date", "Supplier", "Buyer", "Total", "Notes"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._view)

        btn = QHBoxLayout()
        new = QPushButton("New purchase")
        new.clicked.connect(self._new)
        view = QPushButton("View details")
        view.clicked.connect(self._view)
        btn.addWidget(new)
        btn.addWidget(view)
        btn.addStretch()

        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel("Purchases")
        t.setObjectName("pageTitle")
        sub = QLabel("Stock receipts: incoming goods and costs.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addLayout(btn)
        lay.addWidget(self._table)

    def refresh(self) -> None:
        rows = db.list_purchases()
        self._table.setRowCount(0)
        for r in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            vals = [
                r["reference_no"],
                r["purchase_date"],
                r["supplier_name"] or "",
                r["buyer"],
                f"{r['total']:.2f}",
                (r["notes"] or "")[:40],
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

    def _new(self) -> None:
        d = PurchaseDialog(self, self._user_id)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _view(self) -> None:
        pid = self._selected_id()
        if pid is None:
            QMessageBox.information(self, "Purchases", "Select a purchase.")
            return
        p, _ = db.get_purchase(pid)
        if not p:
            QMessageBox.warning(self, "Purchase", "Record not found.")
            return
        dlg = PurchaseViewDialog(self, pid)
        dlg.exec()
