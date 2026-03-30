from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.customers_page import CustomersPage
from ui.dashboard import DashboardPage
from ui.products_page import ProductsPage
from ui.purchases_page import PurchasesPage
from ui.reports_page import ReportsPage
from ui.sales_page import SalesPage
from ui.services_page import ServicesPage
from ui.styles import APP_STYLESHEET
from ui.suppliers_page import SuppliersPage
from ui.users_page import UsersPage


class MainWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self._user = user
        self.setWindowTitle(f"Shop Inventory — {user.get('full_name', user.get('username', ''))}")
        self.setMinimumSize(1100, 740)
        self.setStyleSheet(APP_STYLESHEET)

        self._nav = QListWidget()
        self._nav.setObjectName("navList")
        self._nav.setFixedWidth(232)
        self._nav.setSpacing(1)
        entries = [
            ("Dashboard", "all"),
            ("Products", "all"),
            ("Services", "all"),
            ("Customers", "all"),
            ("Suppliers", "all"),
            ("Sales", "all"),
            ("Purchases", "all"),
            ("Reports", "all"),
            ("Users", "admin"),
        ]
        for label, role in entries:
            if role == "admin" and user.get("role") != "admin":
                continue
            QListWidgetItem(label, self._nav)

        self._stack = QStackedWidget()
        self._dashboard = DashboardPage(self)
        self._products = ProductsPage(self)
        self._services = ServicesPage(self)
        self._customers = CustomersPage(self)
        self._suppliers = SuppliersPage(self)
        self._sales = SalesPage(self, user["id"])
        self._purchases = PurchasesPage(self, user["id"])
        self._reports = ReportsPage(self)
        self._users = UsersPage(self, user) if user.get("role") == "admin" else None

        self._stack.addWidget(self._dashboard)
        self._stack.addWidget(self._products)
        self._stack.addWidget(self._services)
        self._stack.addWidget(self._customers)
        self._stack.addWidget(self._suppliers)
        self._stack.addWidget(self._sales)
        self._stack.addWidget(self._purchases)
        self._stack.addWidget(self._reports)
        if self._users:
            self._stack.addWidget(self._users)

        self._nav.currentRowChanged.connect(self._on_nav)

        brand = QLabel("Inventory")
        brand.setObjectName("brandTitle")
        tag = QLabel("Shop management")
        tag.setObjectName("brandTagline")

        nav_hdr = QLabel("Navigate")
        nav_hdr.setObjectName("navSection")

        logout = QPushButton("Log out")
        logout.setObjectName("logoutBtn")
        logout.clicked.connect(self._logout)

        user_lbl = QLabel(user.get("full_name", user.get("username", "")))
        user_lbl.setStyleSheet("color: #a8a29e; font-size: 12px; padding: 8px 4px 4px 4px;")

        side_lay = QVBoxLayout()
        side_lay.setContentsMargins(18, 22, 18, 20)
        side_lay.setSpacing(0)
        side_lay.addWidget(brand)
        side_lay.addWidget(tag)
        side_lay.addSpacing(8)
        side_lay.addWidget(nav_hdr)
        side_lay.addWidget(self._nav)
        side_lay.addStretch()
        side_lay.addWidget(user_lbl)
        side_lay.addWidget(logout)

        side = QFrame()
        side.setObjectName("sidePanel")
        side.setLayout(side_lay)
        side.setMinimumWidth(232)

        content_wrap = QFrame()
        content_wrap.setObjectName("contentShell")
        cw_lay = QVBoxLayout(content_wrap)
        cw_lay.setContentsMargins(28, 24, 32, 28)
        cw_lay.addWidget(self._stack)

        content = QHBoxLayout()
        content.setSpacing(0)
        content.setContentsMargins(0, 0, 0, 0)
        content.addWidget(side)
        content.addWidget(content_wrap, stretch=1)

        central = QWidget()
        central.setLayout(content)
        self.setCentralWidget(central)

        self._nav.setCurrentRow(0)

    def _on_nav(self, row: int) -> None:
        if row < 0:
            return
        self._stack.setCurrentIndex(row)
        w = self._stack.currentWidget()
        if hasattr(w, "refresh"):
            w.refresh()

    def _logout(self) -> None:
        self.close()
