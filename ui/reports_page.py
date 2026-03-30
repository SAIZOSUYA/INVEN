from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.styles import APP_STYLESHEET


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_STYLESHEET)

        self._report = QComboBox()
        self._report.addItem("Sales by day", "sales_day")
        self._report.addItem("Top selling products", "top_products")
        self._report.addItem("Stock valuation", "stock_val")
        self._report.addItem("Low stock / reorder", "low_stock")

        self._from = QDateEdit()
        self._from.setCalendarPopup(True)
        self._from.setDate(QDate(date.today().year, date.today().month, 1))
        self._from.setDisplayFormat("yyyy-MM-dd")
        self._to = QDateEdit()
        self._to.setCalendarPopup(True)
        self._to.setDate(QDate.currentDate())
        self._to.setDisplayFormat("yyyy-MM-dd")

        self._table = QTableWidget(0, 1)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        form = QFormLayout()
        form.addRow("Report", self._report)
        form.addRow("From", self._from)
        form.addRow("To", self._to)

        run = QPushButton("Run report")
        run.clicked.connect(self._run)

        top = QHBoxLayout()
        top.addLayout(form)
        top.addStretch()
        top.addWidget(run)

        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel("Reports")
        t.setObjectName("pageTitle")
        sub = QLabel("Sales trends, stock value, and reorder alerts.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addLayout(top)
        lay.addWidget(self._table)

        self._report.currentIndexChanged.connect(self._toggle_dates)
        self._toggle_dates()

    def _toggle_dates(self) -> None:
        kind = self._report.currentData()
        use_dates = kind == "sales_day"
        self._from.setEnabled(use_dates)
        self._to.setEnabled(use_dates)

    def refresh(self) -> None:
        self._run()

    def _run(self) -> None:
        kind = self._report.currentData()
        self._table.clear()
        self._table.setRowCount(0)
        if kind == "sales_day":
            start = self._from.date().toString("yyyy-MM-dd")
            end = self._to.date().toString("yyyy-MM-dd")
            rows = db.report_sales_by_day(start, end)
            self._table.setColumnCount(3)
            self._table.setHorizontalHeaderLabels(["Date", "# Sales", "Revenue"])
            for r in rows:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._table.setItem(row, 0, QTableWidgetItem(r["day"]))
                self._table.setItem(row, 1, QTableWidgetItem(str(r["num_sales"])))
                self._table.setItem(row, 2, QTableWidgetItem(f"{float(r['revenue']):.2f}"))
        elif kind == "top_products":
            rows = db.report_top_products(30)
            self._table.setColumnCount(4)
            self._table.setHorizontalHeaderLabels(["SKU", "Name", "Qty sold", "Revenue"])
            for r in rows:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._table.setItem(row, 0, QTableWidgetItem(r["sku"]))
                self._table.setItem(row, 1, QTableWidgetItem(r["name"]))
                self._table.setItem(row, 2, QTableWidgetItem(f"{float(r['qty_sold']):.3f}"))
                self._table.setItem(row, 3, QTableWidgetItem(f"{float(r['revenue']):.2f}"))
        elif kind == "stock_val":
            rows = db.report_stock_valuation()
            self._table.setColumnCount(7)
            self._table.setHorizontalHeaderLabels(
                ["SKU", "Name", "Qty", "Cost", "Retail", "Value (cost)", "Value (retail)"]
            )
            for r in rows:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._table.setItem(row, 0, QTableWidgetItem(r["sku"]))
                self._table.setItem(row, 1, QTableWidgetItem(r["name"]))
                self._table.setItem(row, 2, QTableWidgetItem(f"{float(r['stock_qty']):.3f}"))
                self._table.setItem(row, 3, QTableWidgetItem(f"{float(r['cost_price']):.2f}"))
                self._table.setItem(row, 4, QTableWidgetItem(f"{float(r['selling_price']):.2f}"))
                self._table.setItem(row, 5, QTableWidgetItem(f"{float(r['stock_value_cost']):.2f}"))
                self._table.setItem(row, 6, QTableWidgetItem(f"{float(r['stock_value_retail']):.2f}"))
        elif kind == "low_stock":
            rows = db.report_low_stock()
            self._table.setColumnCount(5)
            self._table.setHorizontalHeaderLabels(["SKU", "Name", "Stock", "Reorder", "Unit"])
            for r in rows:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._table.setItem(row, 0, QTableWidgetItem(r["sku"]))
                self._table.setItem(row, 1, QTableWidgetItem(r["name"]))
                self._table.setItem(row, 2, QTableWidgetItem(f"{float(r['stock_qty']):.3f}"))
                self._table.setItem(row, 3, QTableWidgetItem(f"{float(r['reorder_level']):.3f}"))
                self._table.setItem(row, 4, QTableWidgetItem(r["unit"]))
