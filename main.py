"""Shop inventory — PyQt6 + SQLite."""
import sys

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

import database as db
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow


def main() -> int:
    db.init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("Shop Inventory")

    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        return 0

    username, password = login.credentials()
    user = db.authenticate(username, password)
    if not user:
        QMessageBox.critical(None, "Login", "Invalid username or password.")
        return 1

    win = MainWindow(user)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
