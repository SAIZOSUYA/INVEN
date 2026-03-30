from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel, QPushButton, QVBoxLayout, QWidget

import database as db
from ui.styles import APP_STYLESHEET


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_STYLESHEET)
        self._labels: dict[str, QLabel] = {}

        grid = QGridLayout()
        grid.setSpacing(18)
        grid.setContentsMargins(0, 8, 0, 0)

        stats = [
            ("today_sales", "Today's sales", "stat"),
            ("month_sales", "This month's sales", "stat"),
            ("product_count", "Products in catalog", "stat"),
            ("low_stock", "Items at or below reorder", "stat"),
            ("customer_count", "Customers", "stat"),
        ]

        for i, (key, title, _) in enumerate(stats):
            box = QGroupBox(title)
            lay = QVBoxLayout(box)
            lay.setSpacing(6)
            val = QLabel("—")
            val.setObjectName("stat")
            val.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self._labels[key] = val
            lay.addWidget(val)
            grid.addWidget(box, i // 3, i % 3)

        refresh = QPushButton("Refresh dashboard")
        refresh.clicked.connect(self.refresh)

        outer = QVBoxLayout(self)
        outer.setSpacing(8)
        outer.setContentsMargins(0, 0, 0, 0)

        t = QLabel("Dashboard")
        t.setObjectName("pageTitle")
        sub = QLabel("Overview of sales, catalog, and stock at a glance.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)

        outer.addWidget(t)
        outer.addWidget(sub)
        outer.addSpacing(4)
        outer.addLayout(grid)
        outer.addWidget(refresh)
        outer.addStretch()

    def refresh(self) -> None:
        s = db.dashboard_stats()
        self._labels["today_sales"].setText(f"{s['today_sales']:.2f}")
        self._labels["month_sales"].setText(f"{s['month_sales']:.2f}")
        self._labels["product_count"].setText(str(s["product_count"]))
        self._labels["low_stock"].setText(str(s["low_stock"]))
        self._labels["customer_count"].setText(str(s["customer_count"]))
