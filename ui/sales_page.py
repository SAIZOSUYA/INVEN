from __future__ import annotations

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
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


class SaleViewDialog(QDialog):
    def __init__(self, parent=None, sale_id: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Sale details")
        self.setMinimumSize(560, 420)
        self.setStyleSheet(APP_STYLESHEET)
        s, items = db.get_sale(sale_id)
        assert s is not None
        info = QLabel(
            f"<b>{s['invoice_no']}</b> &nbsp; Date: {s['sale_date']} &nbsp; "
            f"Customer: {s['customer_name'] or '—'} &nbsp; Seller: {s['seller']}<br>"
            f"Payment: {s['payment_method']} &nbsp; Subtotal: {s['subtotal']:.2f} &nbsp; "
            f"Tax: {s['tax_amount']:.2f} &nbsp; Discount: {s['discount']:.2f} &nbsp; <b>Total: {s['total']:.2f}</b>"
        )
        info.setWordWrap(True)
        tbl = QTableWidget(0, 6)
        tbl.setHorizontalHeaderLabels(["Type", "Item", "Qty", "Unit price", "Line total", "Note"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for it in items:
            row = tbl.rowCount()
            tbl.insertRow(row)
            typ = it["item_type"]
            name = ""
            if typ == "product" and it["product_id"]:
                p = db.get_product(it["product_id"])
                name = p["name"] if p else "?"
            elif typ == "service" and it["service_id"]:
                for sv in db.list_services(""):
                    if sv["id"] == it["service_id"]:
                        name = sv["name"]
                        break
            tbl.setItem(row, 0, QTableWidgetItem(typ))
            tbl.setItem(row, 1, QTableWidgetItem(name))
            tbl.setItem(row, 2, QTableWidgetItem(str(it["qty"])))
            tbl.setItem(row, 3, QTableWidgetItem(f"{it['unit_price']:.2f}"))
            tbl.setItem(row, 4, QTableWidgetItem(f"{it['line_total']:.2f}"))
            tbl.setItem(row, 5, QTableWidgetItem(it["description"] or ""))
        notes = QLabel(s["notes"] or "")
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        lay = QVBoxLayout(self)
        lay.addWidget(info)
        lay.addWidget(tbl)
        if s["notes"]:
            lay.addWidget(QLabel("<b>Notes</b>"))
            lay.addWidget(notes)
        lay.addWidget(close_btn)


class SaleDialog(QDialog):
    def __init__(self, parent=None, user_id: int = 1):
        super().__init__(parent)
        self._user_id = user_id
        self.setWindowTitle("New sale")
        self.setMinimumSize(720, 480)
        self.setStyleSheet(APP_STYLESHEET)

        self._cust = QComboBox()
        self._cust.addItem("Walk-in / none", None)
        for c in db.list_customers(""):
            self._cust.addItem(c["name"], c["id"])

        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDate(QDate.currentDate())
        self._date.setDisplayFormat("yyyy-MM-dd")

        self._tax = QDoubleSpinBox()
        self._tax.setMaximum(100)
        self._tax.setDecimals(2)
        self._tax.setSuffix(" %")
        self._tax.setValue(0.0)

        self._disc = QDoubleSpinBox()
        self._disc.setMaximum(1e9)
        self._disc.setDecimals(2)
        self._disc.setValue(0.0)

        self._pay = QComboBox()
        for x in ("cash", "card", "transfer", "other"):
            self._pay.addItem(x.title(), x)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(60)

        self._products = {r["id"]: r for r in db.list_products("")}
        self._services = {r["id"]: r for r in db.list_services("")}

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Type", "Item", "Qty", "Unit price", "Line"])
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
        form.addWidget(QLabel("Customer"), 0, 0)
        form.addWidget(self._cust, 0, 1)
        form.addWidget(QLabel("Sale date"), 0, 2)
        form.addWidget(self._date, 0, 3)
        form.addWidget(QLabel("Tax %"), 1, 0)
        form.addWidget(self._tax, 1, 1)
        form.addWidget(QLabel("Discount"), 1, 2)
        form.addWidget(self._disc, 1, 3)
        form.addWidget(QLabel("Payment"), 2, 0)
        form.addWidget(self._pay, 2, 1)
        form.addWidget(QLabel("Notes"), 2, 2)
        form.addWidget(self._notes, 2, 3)

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
        self._table.cellChanged.connect(self._recalc)

    def _make_type_combo(self) -> QComboBox:
        cb = QComboBox()
        cb.addItem("Product", "product")
        cb.addItem("Service", "service")
        cb.currentIndexChanged.connect(self._on_type_changed)
        return cb

    def _item_combo_for_row(self, row: int) -> QComboBox:
        w = self._table.cellWidget(row, 1)
        assert isinstance(w, QComboBox)
        return w

    def _type_combo_for_row(self, row: int) -> QComboBox:
        w = self._table.cellWidget(row, 0)
        assert isinstance(w, QComboBox)
        return w

    def _on_type_changed(self) -> None:
        sender = self.sender()
        if not isinstance(sender, QComboBox):
            return
        for r in range(self._table.rowCount()):
            if self._table.cellWidget(r, 0) is sender:
                self._fill_items(r)
                self._recalc()
                return

    def _fill_items(self, row: int) -> None:
        tcb = self._type_combo_for_row(row)
        icb = self._item_combo_for_row(row)
        icb.blockSignals(True)
        icb.clear()
        kind = tcb.currentData()
        if kind == "product":
            for pid, p in sorted(self._products.items(), key=lambda x: x[1]["name"].lower()):
                icb.addItem(f"{p['sku']} — {p['name']}", pid)
        else:
            for sid, s in sorted(self._services.items(), key=lambda x: x[1]["name"].lower()):
                icb.addItem(f"{s['code']} — {s['name']}", sid)
        icb.blockSignals(False)
        try:
            icb.currentIndexChanged.disconnect()
        except TypeError:
            pass
        icb.currentIndexChanged.connect(self._on_item_changed)

    def _on_item_changed(self) -> None:
        sender = self.sender()
        if not isinstance(sender, QComboBox):
            return
        for r in range(self._table.rowCount()):
            if self._table.cellWidget(r, 1) is sender:
                self._prefill_price(r)
                self._recalc()
                return

    def _prefill_price(self, row: int) -> None:
        tcb = self._type_combo_for_row(row)
        icb = self._item_combo_for_row(row)
        sp = self._table.cellWidget(row, 3)
        assert isinstance(sp, QDoubleSpinBox)
        kind = tcb.currentData()
        iid = icb.currentData()
        if kind == "product" and iid in self._products:
            sp.setValue(float(self._products[iid]["selling_price"]))
        elif kind == "service" and iid in self._services:
            sp.setValue(float(self._services[iid]["price"]))

    def _add_row(self) -> None:
        self._table.blockSignals(True)
        row = self._table.rowCount()
        self._table.insertRow(row)
        tcb = self._make_type_combo()
        icb = QComboBox()
        q = QDoubleSpinBox()
        q.setMaximum(1e9)
        q.setDecimals(3)
        q.setValue(1.0)
        p = QDoubleSpinBox()
        p.setMaximum(1e9)
        p.setDecimals(2)
        lt = QLabel("0.00")
        self._table.setCellWidget(row, 0, tcb)
        self._table.setCellWidget(row, 1, icb)
        self._table.setCellWidget(row, 2, q)
        self._table.setCellWidget(row, 3, p)
        self._table.setCellWidget(row, 4, lt)
        q.valueChanged.connect(self._recalc)
        p.valueChanged.connect(self._recalc)
        self._fill_items(row)
        self._prefill_price(row)
        self._table.blockSignals(False)
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
            q = self._table.cellWidget(r, 2)
            p = self._table.cellWidget(r, 3)
            lt = self._table.cellWidget(r, 4)
            if not isinstance(q, QDoubleSpinBox) or not isinstance(p, QDoubleSpinBox) or not isinstance(lt, QLabel):
                continue
            line = round(q.value() * p.value(), 2)
            lt.setText(f"{line:.2f}")
            sub += line
        tax_amt = round(sub * (self._tax.value() / 100.0), 2) if self._tax.value() else 0.0
        total = round(sub + tax_amt - self._disc.value(), 2)
        self._tot_lbl.setText(f"Subtotal: {sub:.2f}  |  Tax: {tax_amt:.2f}  |  Total: {total:.2f}")

    def _save(self) -> None:
        lines: list[dict] = []
        for r in range(self._table.rowCount()):
            tcb = self._table.cellWidget(r, 0)
            icb = self._table.cellWidget(r, 1)
            q = self._table.cellWidget(r, 2)
            p = self._table.cellWidget(r, 3)
            if not all(isinstance(x, QComboBox) for x in (tcb, icb)) or not isinstance(q, QDoubleSpinBox) or not isinstance(
                p, QDoubleSpinBox
            ):
                continue
            kind = tcb.currentData()
            iid = icb.currentData()
            if iid is None:
                continue
            desc = ""
            if kind == "product":
                lines.append(
                    {
                        "item_type": "product",
                        "product_id": int(iid),
                        "service_id": None,
                        "qty": q.value(),
                        "unit_price": p.value(),
                        "description": desc,
                    }
                )
            else:
                lines.append(
                    {
                        "item_type": "service",
                        "product_id": None,
                        "service_id": int(iid),
                        "qty": q.value(),
                        "unit_price": p.value(),
                        "description": desc,
                    }
                )
        if not lines:
            QMessageBox.warning(self, "Sale", "Add at least one line with an item.")
            return
        try:
            db.create_sale(
                self._user_id,
                self._cust.currentData(),
                self._date.date().toString("yyyy-MM-dd"),
                self._tax.value(),
                self._disc.value(),
                self._pay.currentData(),
                self._notes.toPlainText(),
                lines,
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Sale failed", str(e))


class SalesPage(QWidget):
    def __init__(self, parent=None, user_id: int = 1):
        super().__init__(parent)
        self._user_id = user_id
        self.setStyleSheet(APP_STYLESHEET)
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["Invoice", "Date", "Customer", "Seller", "Total", "Payment", "Notes"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._view)

        btn = QHBoxLayout()
        new = QPushButton("New sale")
        new.clicked.connect(self._new)
        view = QPushButton("View details")
        view.clicked.connect(self._view)
        btn.addWidget(new)
        btn.addWidget(view)
        btn.addStretch()

        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel("Sales")
        t.setObjectName("pageTitle")
        sub = QLabel("Invoices: products, services, tax, and payments.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addLayout(btn)
        lay.addWidget(self._table)

    def refresh(self) -> None:
        rows = db.list_sales()
        self._table.setRowCount(0)
        for r in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            vals = [
                r["invoice_no"],
                r["sale_date"],
                r["customer_name"] or "",
                r["seller"],
                f"{r['total']:.2f}",
                r["payment_method"],
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
        d = SaleDialog(self, self._user_id)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _view(self) -> None:
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, "Sales", "Select a sale.")
            return
        s, _ = db.get_sale(sid)
        if not s:
            QMessageBox.warning(self, "Sale", "Record not found.")
            return
        dlg = SaleViewDialog(self, sid)
        dlg.exec()
