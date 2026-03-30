from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
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


class ProductDialog(QDialog):
    def __init__(self, parent=None, product_id: int | None = None):
        super().__init__(parent)
        self._pid = product_id
        self.setWindowTitle("Edit product" if product_id else "New product")
        self.setMinimumWidth(440)
        self.setStyleSheet(APP_STYLESHEET)

        self._sku = QLineEdit()
        self._name = QLineEdit()
        cat_row = QHBoxLayout()
        self._cat = QComboBox()
        self._cat.addItem("(None)", None)
        for c in db.list_categories():
            self._cat.addItem(c["name"], c["id"])
        new_cat = QPushButton("New…")
        new_cat.setObjectName("secondary")
        new_cat.clicked.connect(self._new_category)
        cat_row.addWidget(self._cat, stretch=1)
        cat_row.addWidget(new_cat)
        self._cost = QDoubleSpinBox()
        self._cost.setMaximum(1e9)
        self._cost.setDecimals(2)
        self._price = QDoubleSpinBox()
        self._price.setMaximum(1e9)
        self._price.setDecimals(2)
        self._stock = QDoubleSpinBox()
        self._stock.setMaximum(1e9)
        self._stock.setDecimals(3)
        self._reorder = QDoubleSpinBox()
        self._reorder.setMaximum(1e9)
        self._reorder.setDecimals(3)
        self._unit = QLineEdit()
        self._unit.setPlaceholderText("pcs")
        self._barcode = QLineEdit()
        self._notes = QTextEdit()
        self._notes.setMaximumHeight(80)

        form = QFormLayout()
        form.addRow("SKU *", self._sku)
        form.addRow("Name *", self._name)
        form.addRow("Category", cat_row)
        form.addRow("Cost price", self._cost)
        form.addRow("Selling price", self._price)
        form.addRow("Stock qty", self._stock)
        form.addRow("Reorder level", self._reorder)
        form.addRow("Unit", self._unit)
        form.addRow("Barcode", self._barcode)
        form.addRow("Notes", self._notes)

        if product_id:
            p = db.get_product(product_id)
            if p:
                self._sku.setText(p["sku"])
                self._name.setText(p["name"])
                idx = self._cat.findData(p["category_id"])
                if idx >= 0:
                    self._cat.setCurrentIndex(idx)
                self._cost.setValue(float(p["cost_price"]))
                self._price.setValue(float(p["selling_price"]))
                self._stock.setValue(float(p["stock_qty"]))
                self._reorder.setValue(float(p["reorder_level"]))
                self._unit.setText(p["unit"] or "pcs")
                self._barcode.setText(p["barcode"] or "")
                self._notes.setPlainText(p["notes"] or "")

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(bb)

    def _new_category(self) -> None:
        name, ok = QInputDialog.getText(self, "New category", "Category name:")
        if not ok or not name.strip():
            return
        try:
            db.add_category(name)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self._cat.clear()
        self._cat.addItem("(None)", None)
        for c in db.list_categories():
            self._cat.addItem(c["name"], c["id"])
        idx = self._cat.findText(name.strip())
        if idx >= 0:
            self._cat.setCurrentIndex(idx)

    def _save(self) -> None:
        if not self._sku.text().strip() or not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "SKU and name are required.")
            return
        try:
            db.save_product(
                self._pid,
                self._sku.text(),
                self._name.text(),
                self._cat.currentData(),
                self._cost.value(),
                self._price.value(),
                self._stock.value(),
                self._reorder.value(),
                self._unit.text() or "pcs",
                self._barcode.text(),
                self._notes.toPlainText(),
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class ProductsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_STYLESHEET)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search SKU, name, barcode…")
        self._search.returnPressed.connect(self.refresh)

        self._table = QTableWidget(0, 9)
        self._table.setHorizontalHeaderLabels(
            ["SKU", "Name", "Category", "Cost", "Price", "Stock", "Reorder", "Unit", "Barcode"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)

        btn_row = QHBoxLayout()
        add = QPushButton("Add product")
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
        t = QLabel("Products")
        t.setObjectName("pageTitle")
        sub = QLabel("SKUs, pricing, categories, and stock levels.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addLayout(btn_row)
        lay.addWidget(self._table)

    def refresh(self) -> None:
        rows = db.list_products(self._search.text())
        self._table.setRowCount(0)
        for r in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            vals = [
                r["sku"],
                r["name"],
                r["category_name"] or "",
                f"{r['cost_price']:.2f}",
                f"{r['selling_price']:.2f}",
                f"{r['stock_qty']:.3f}",
                f"{r['reorder_level']:.3f}",
                r["unit"],
                r["barcode"] or "",
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
        d = ProductDialog(self, None)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit(self) -> None:
        pid = self._selected_id()
        if pid is None:
            QMessageBox.information(self, "Products", "Select a product row.")
            return
        d = ProductDialog(self, pid)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        if QMessageBox.question(self, "Confirm", "Delete this product?") != QMessageBox.StandardButton.Yes:
            return
        try:
            db.delete_product(pid)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
