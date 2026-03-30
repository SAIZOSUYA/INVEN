"""SQLite persistence for the inventory application."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any

from auth import hash_password, verify_password

DB_PATH = Path(__file__).resolve().parent / "inventory.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                role TEXT NOT NULL DEFAULT 'staff' CHECK(role IN ('admin', 'staff')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                cost_price REAL NOT NULL DEFAULT 0,
                selling_price REAL NOT NULL DEFAULT 0,
                stock_qty REAL NOT NULL DEFAULT 0,
                reorder_level REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL DEFAULT 'pcs',
                barcode TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0,
                duration_minutes INTEGER,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT NOT NULL UNIQUE,
                customer_id INTEGER REFERENCES customers(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                sale_date TEXT NOT NULL,
                subtotal REAL NOT NULL DEFAULT 0,
                tax_rate REAL NOT NULL DEFAULT 0,
                tax_amount REAL NOT NULL DEFAULT 0,
                discount REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                payment_method TEXT NOT NULL DEFAULT 'cash',
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
                item_type TEXT NOT NULL CHECK(item_type IN ('product', 'service')),
                product_id INTEGER REFERENCES products(id),
                service_id INTEGER REFERENCES services(id),
                description TEXT,
                qty REAL NOT NULL DEFAULT 1,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_no TEXT NOT NULL UNIQUE,
                supplier_id INTEGER REFERENCES suppliers(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                purchase_date TEXT NOT NULL,
                subtotal REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                qty REAL NOT NULL,
                unit_cost REAL NOT NULL,
                line_total REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
            CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
            CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(purchase_date);
            """
        )

        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        if row and row["c"] == 0:
            ph, salt = hash_password("admin123")
            conn.execute(
                """
                INSERT INTO users (username, password_hash, salt, full_name, role)
                VALUES (?, ?, ?, ?, 'admin')
                """,
                ("admin", ph, salt, "Administrator"),
            )
        cats = conn.execute("SELECT COUNT(*) AS c FROM categories").fetchone()
        if cats and cats["c"] == 0:
            for n in ("General", "Electronics", "Groceries", "Services"):
                conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (n,))


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username.strip(),),
        ).fetchone()
        if not row:
            return None
        if not verify_password(password, row["password_hash"], row["salt"]):
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"] or row["username"],
            "role": row["role"],
        }


def list_users() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(conn.execute("SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY username"))


def create_user(username: str, password: str, full_name: str, role: str) -> None:
    ph, salt = hash_password(password)
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, salt, full_name, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username.strip(), ph, salt, full_name.strip() or username, role),
        )


def update_user(uid: int, full_name: str, role: str, is_active: int) -> None:
    with transaction() as conn:
        conn.execute(
            "UPDATE users SET full_name = ?, role = ?, is_active = ? WHERE id = ?",
            (full_name.strip(), role, is_active, uid),
        )


def set_user_password(uid: int, password: str) -> None:
    ph, salt = hash_password(password)
    with transaction() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (ph, salt, uid),
        )


def list_categories() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(conn.execute("SELECT * FROM categories ORDER BY name"))


def add_category(name: str) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))


def list_products(search: str = "") -> list[sqlite3.Row]:
    q = "%" + search.strip() + "%"
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT p.*, c.name AS category_name
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                WHERE p.sku LIKE ? OR p.name LIKE ? OR IFNULL(p.barcode,'') LIKE ?
                ORDER BY p.name
                """,
                (q, q, q),
            )
        )


def save_product(
    pid: int | None,
    sku: str,
    name: str,
    category_id: int | None,
    cost_price: float,
    selling_price: float,
    stock_qty: float,
    reorder_level: float,
    unit: str,
    barcode: str,
    notes: str,
) -> int:
    with transaction() as conn:
        if pid:
            conn.execute(
                """
                UPDATE products SET sku=?, name=?, category_id=?, cost_price=?, selling_price=?,
                stock_qty=?, reorder_level=?, unit=?, barcode=?, notes=?
                WHERE id=?
                """,
                (
                    sku.strip(),
                    name.strip(),
                    category_id,
                    cost_price,
                    selling_price,
                    stock_qty,
                    reorder_level,
                    unit.strip() or "pcs",
                    barcode.strip() or None,
                    notes.strip() or None,
                    pid,
                ),
            )
            return pid
        cur = conn.execute(
            """
            INSERT INTO products (sku, name, category_id, cost_price, selling_price, stock_qty, reorder_level, unit, barcode, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sku.strip(),
                name.strip(),
                category_id,
                cost_price,
                selling_price,
                stock_qty,
                reorder_level,
                unit.strip() or "pcs",
                barcode.strip() or None,
                notes.strip() or None,
            ),
        )
        return int(cur.lastrowid)


def delete_product(pid: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (pid,))


def get_product(pid: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()


def list_services(search: str = "") -> list[sqlite3.Row]:
    q = "%" + search.strip() + "%"
    with get_connection() as conn:
        return list(
            conn.execute(
                "SELECT * FROM services WHERE code LIKE ? OR name LIKE ? ORDER BY name",
                (q, q),
            )
        )


def save_service(
    sid: int | None,
    code: str,
    name: str,
    price: float,
    duration_minutes: int | None,
    description: str,
    is_active: int,
) -> int:
    with transaction() as conn:
        if sid:
            conn.execute(
                """
                UPDATE services SET code=?, name=?, price=?, duration_minutes=?, description=?, is_active=?
                WHERE id=?
                """,
                (
                    code.strip(),
                    name.strip(),
                    price,
                    duration_minutes,
                    description.strip() or None,
                    is_active,
                    sid,
                ),
            )
            return sid
        cur = conn.execute(
            """
            INSERT INTO services (code, name, price, duration_minutes, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (code.strip(), name.strip(), price, duration_minutes, description.strip() or None, is_active),
        )
        return int(cur.lastrowid)


def delete_service(sid: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM services WHERE id = ?", (sid,))


def list_customers(search: str = "") -> list[sqlite3.Row]:
    q = "%" + search.strip() + "%"
    with get_connection() as conn:
        return list(
            conn.execute(
                "SELECT * FROM customers WHERE name LIKE ? OR IFNULL(phone,'') LIKE ? ORDER BY name",
                (q, q),
            )
        )


def save_customer(cid: int | None, name: str, phone: str, email: str, address: str, notes: str) -> int:
    with transaction() as conn:
        if cid:
            conn.execute(
                """
                UPDATE customers SET name=?, phone=?, email=?, address=?, notes=? WHERE id=?
                """,
                (
                    name.strip(),
                    phone.strip() or None,
                    email.strip() or None,
                    address.strip() or None,
                    notes.strip() or None,
                    cid,
                ),
            )
            return cid
        cur = conn.execute(
            """
            INSERT INTO customers (name, phone, email, address, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                phone.strip() or None,
                email.strip() or None,
                address.strip() or None,
                notes.strip() or None,
            ),
        )
        return int(cur.lastrowid)


def delete_customer(cid: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM customers WHERE id = ?", (cid,))


def list_suppliers(search: str = "") -> list[sqlite3.Row]:
    q = "%" + search.strip() + "%"
    with get_connection() as conn:
        return list(
            conn.execute(
                "SELECT * FROM suppliers WHERE name LIKE ? OR IFNULL(phone,'') LIKE ? ORDER BY name",
                (q, q),
            )
        )


def save_supplier(sid: int | None, name: str, phone: str, email: str, address: str, notes: str) -> int:
    with transaction() as conn:
        if sid:
            conn.execute(
                """
                UPDATE suppliers SET name=?, phone=?, email=?, address=?, notes=? WHERE id=?
                """,
                (
                    name.strip(),
                    phone.strip() or None,
                    email.strip() or None,
                    address.strip() or None,
                    notes.strip() or None,
                    sid,
                ),
            )
            return sid
        cur = conn.execute(
            """
            INSERT INTO suppliers (name, phone, email, address, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                phone.strip() or None,
                email.strip() or None,
                address.strip() or None,
                notes.strip() or None,
            ),
        )
        return int(cur.lastrowid)


def delete_supplier(sid: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM suppliers WHERE id = ?", (sid,))


def _next_invoice_no(conn: sqlite3.Connection) -> str:
    y = datetime.now().year
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM sales WHERE invoice_no LIKE ?",
        (f"INV-{y}-%",),
    ).fetchone()
    n = (row["c"] if row else 0) + 1
    return f"INV-{y}-{n:05d}"


def _next_purchase_ref(conn: sqlite3.Connection) -> str:
    y = datetime.now().year
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM purchases WHERE reference_no LIKE ?",
        (f"PO-{y}-%",),
    ).fetchone()
    n = (row["c"] if row else 0) + 1
    return f"PO-{y}-{n:05d}"


def create_sale(
    user_id: int,
    customer_id: int | None,
    sale_date: str,
    tax_rate: float,
    discount: float,
    payment_method: str,
    notes: str,
    lines: list[dict[str, Any]],
) -> int:
    """lines: item_type, product_id|service_id, qty, unit_price, description."""
    with transaction() as conn:
        inv = _next_invoice_no(conn)
        subtotal = 0.0
        prepared: list[dict[str, Any]] = []
        for line in lines:
            qty = float(line["qty"])
            unit = float(line["unit_price"])
            lt = round(qty * unit, 2)
            subtotal += lt
            prepared.append({**line, "line_total": lt, "qty": qty, "unit_price": unit})

        tax_amount = round(subtotal * (tax_rate / 100.0), 2) if tax_rate else 0.0
        total = round(subtotal + tax_amount - float(discount), 2)

        cur = conn.execute(
            """
            INSERT INTO sales (invoice_no, customer_id, user_id, sale_date, subtotal, tax_rate, tax_amount, discount, total, payment_method, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inv,
                customer_id,
                user_id,
                sale_date,
                subtotal,
                tax_rate,
                tax_amount,
                discount,
                total,
                payment_method,
                notes.strip() or None,
            ),
        )
        sale_id = int(cur.lastrowid)

        for line in prepared:
            it = line["item_type"]
            pid = line.get("product_id")
            sid = line.get("service_id")
            desc = line.get("description") or ""

            if it == "product" and pid:
                pr = conn.execute("SELECT stock_qty, name FROM products WHERE id = ?", (pid,)).fetchone()
                if not pr:
                    raise ValueError("Product not found")
                if float(pr["stock_qty"]) < float(line["qty"]):
                    raise ValueError(f"Insufficient stock for {pr['name']}")
                conn.execute(
                    "UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?",
                    (line["qty"], pid),
                )

            conn.execute(
                """
                INSERT INTO sale_items (sale_id, item_type, product_id, service_id, description, qty, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    it,
                    pid if it == "product" else None,
                    sid if it == "service" else None,
                    desc,
                    line["qty"],
                    line["unit_price"],
                    line["line_total"],
                ),
            )
        return sale_id


def list_sales(limit: int = 200) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT s.*, u.username AS seller, c.name AS customer_name
                FROM sales s
                JOIN users u ON u.id = s.user_id
                LEFT JOIN customers c ON c.id = s.customer_id
                ORDER BY s.sale_date DESC, s.id DESC
                LIMIT ?
                """,
                (limit,),
            )
        )


def get_sale(sale_id: int) -> tuple[sqlite3.Row | None, list[sqlite3.Row]]:
    with get_connection() as conn:
        s = conn.execute(
            """
            SELECT s.*, u.username AS seller, c.name AS customer_name
            FROM sales s
            JOIN users u ON u.id = s.user_id
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE s.id = ?
            """,
            (sale_id,),
        ).fetchone()
        items = list(conn.execute("SELECT * FROM sale_items WHERE sale_id = ? ORDER BY id", (sale_id,)))
        return s, items


def create_purchase(
    user_id: int,
    supplier_id: int | None,
    purchase_date: str,
    notes: str,
    lines: list[dict[str, Any]],
) -> int:
    with transaction() as conn:
        ref = _next_purchase_ref(conn)
        subtotal = 0.0
        prepared: list[dict[str, Any]] = []
        for line in lines:
            qty = float(line["qty"])
            uc = float(line["unit_cost"])
            lt = round(qty * uc, 2)
            subtotal += lt
            prepared.append({**line, "line_total": lt, "qty": qty, "unit_cost": uc})

        total = round(subtotal, 2)
        cur = conn.execute(
            """
            INSERT INTO purchases (reference_no, supplier_id, user_id, purchase_date, subtotal, total, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ref, supplier_id, user_id, purchase_date, subtotal, total, notes.strip() or None),
        )
        pur_id = int(cur.lastrowid)

        for line in prepared:
            pid = line["product_id"]
            conn.execute(
                "UPDATE products SET stock_qty = stock_qty + ?, cost_price = ? WHERE id = ?",
                (line["qty"], line["unit_cost"], pid),
            )
            conn.execute(
                """
                INSERT INTO purchase_items (purchase_id, product_id, qty, unit_cost, line_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pur_id, pid, line["qty"], line["unit_cost"], line["line_total"]),
            )
        return pur_id


def list_purchases(limit: int = 200) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT p.*, u.username AS buyer, s.name AS supplier_name
                FROM purchases p
                JOIN users u ON u.id = p.user_id
                LEFT JOIN suppliers s ON s.id = p.supplier_id
                ORDER BY p.purchase_date DESC, p.id DESC
                LIMIT ?
                """,
                (limit,),
            )
        )


def get_purchase(purchase_id: int) -> tuple[sqlite3.Row | None, list[sqlite3.Row]]:
    with get_connection() as conn:
        p = conn.execute(
            """
            SELECT p.*, u.username AS buyer, s.name AS supplier_name
            FROM purchases p
            JOIN users u ON u.id = p.user_id
            LEFT JOIN suppliers s ON s.id = p.supplier_id
            WHERE p.id = ?
            """,
            (purchase_id,),
        ).fetchone()
        items = list(
            conn.execute(
                """
                SELECT pi.*, pr.name AS product_name, pr.sku
                FROM purchase_items pi
                JOIN products pr ON pr.id = pi.product_id
                WHERE pi.purchase_id = ?
                ORDER BY pi.id
                """,
                (purchase_id,),
            )
        )
        return p, items


def dashboard_stats() -> dict[str, Any]:
    today = date.today().isoformat()
    month_start = date(date.today().year, date.today().month, 1).isoformat()
    with get_connection() as conn:
        t_sales = conn.execute(
            "SELECT COALESCE(SUM(total), 0) AS v FROM sales WHERE sale_date = ?",
            (today,),
        ).fetchone()["v"]
        m_sales = conn.execute(
            "SELECT COALESCE(SUM(total), 0) AS v FROM sales WHERE sale_date >= ?",
            (month_start,),
        ).fetchone()["v"]
        n_products = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        low = conn.execute(
            "SELECT COUNT(*) AS c FROM products WHERE stock_qty <= reorder_level"
        ).fetchone()["c"]
        n_cust = conn.execute("SELECT COUNT(*) AS c FROM customers").fetchone()["c"]
    return {
        "today_sales": float(t_sales),
        "month_sales": float(m_sales),
        "product_count": int(n_products),
        "low_stock": int(low),
        "customer_count": int(n_cust),
    }


def report_sales_by_day(start: str, end: str) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT sale_date AS day, COUNT(*) AS num_sales, COALESCE(SUM(total),0) AS revenue
                FROM sales
                WHERE sale_date >= ? AND sale_date <= ?
                GROUP BY sale_date
                ORDER BY sale_date
                """,
                (start, end),
            )
        )


def report_top_products(limit: int = 20) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT pr.sku, pr.name,
                       SUM(si.qty) AS qty_sold,
                       SUM(si.line_total) AS revenue
                FROM sale_items si
                JOIN products pr ON pr.id = si.product_id
                WHERE si.item_type = 'product'
                GROUP BY pr.id
                ORDER BY revenue DESC
                LIMIT ?
                """,
                (limit,),
            )
        )


def report_stock_valuation() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT sku, name, stock_qty, cost_price, selling_price,
                       (stock_qty * cost_price) AS stock_value_cost,
                       (stock_qty * selling_price) AS stock_value_retail
                FROM products
                ORDER BY name
                """
            )
        )


def report_low_stock() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT sku, name, stock_qty, reorder_level, unit
                FROM products
                WHERE stock_qty <= reorder_level
                ORDER BY stock_qty ASC, name
                """
            )
        )
