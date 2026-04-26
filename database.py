import sqlite3
from datetime import datetime


class Database:
    def __init__(self):
        self.db_name = "qurilishlink.db"
        self.init_db()

    def get_conn(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_conn()
        c = conn.cursor()

        # Users table — stores role (supplier/buyer)
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                company TEXT,
                role TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Suppliers table — stores location and contact
        c.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                company TEXT,
                contact TEXT,
                latitude REAL,
                longitude REAL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Products table — each supplier can have multiple products
        c.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER,
                material TEXT,
                price_per_unit REAL,
                unit TEXT DEFAULT 'unit',
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        """)

        # Buyers table
        c.execute("""
            CREATE TABLE IF NOT EXISTS buyers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                company TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Orders table
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_telegram_id INTEGER,
                buyer_name TEXT,
                supplier_id INTEGER,
                supplier_name TEXT,
                product_id INTEGER,
                material TEXT,
                quantity INTEGER,
                price_per_unit REAL,
                total_cost REAL,
                commission REAL,
                status TEXT DEFAULT 'Pending',
                placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ── User methods ─────────────────────────────────────────────────────
    def get_user_role(self, telegram_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT role FROM users WHERE telegram_id=?", (telegram_id,)
        ).fetchone()
        conn.close()
        return result[0] if result else None

    def register_user(self, telegram_id, name, company, role):
        conn = self.get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO users (telegram_id, name, company, role) VALUES (?,?,?,?)",
            (telegram_id, name, company, role)
        )
        conn.commit()
        conn.close()

    def get_all_users(self):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT telegram_id, name, company, role, registered_at FROM users"
        ).fetchall()
        conn.close()
        return result

    # ── Supplier methods ─────────────────────────────────────────────────
    def add_supplier(self, telegram_id, name, company, contact, latitude, longitude):
        conn = self.get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO suppliers (telegram_id, name, company, contact, latitude, longitude) VALUES (?,?,?,?,?,?)",
            (telegram_id, name, company, contact, latitude, longitude)
        )
        conn.commit()
        conn.close()

    def get_supplier_by_telegram_id(self, telegram_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, name, company, contact, latitude, longitude FROM suppliers WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()
        conn.close()
        return result

    def get_supplier_by_id(self, supplier_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, name, company, contact, latitude, longitude FROM suppliers WHERE id=?",
            (supplier_id,)
        ).fetchone()
        conn.close()
        return result

    def get_all_suppliers(self):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, name, company, contact, latitude, longitude FROM suppliers"
        ).fetchall()
        conn.close()
        return result

    # ── Product methods ──────────────────────────────────────────────────
    def add_product(self, supplier_id, material, price_per_unit, unit="unit"):
        conn = self.get_conn()
        conn.execute(
            "INSERT INTO products (supplier_id, material, price_per_unit, unit) VALUES (?,?,?,?)",
            (supplier_id, material, price_per_unit, unit)
        )
        conn.commit()
        conn.close()

    def get_supplier_products(self, supplier_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, material, price_per_unit, unit FROM products WHERE supplier_id=?",
            (supplier_id,)
        ).fetchall()
        conn.close()
        return result

    def get_product_by_id(self, product_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, supplier_id, material, price_per_unit, unit FROM products WHERE id=?",
            (product_id,)
        ).fetchone()
        conn.close()
        return result

    def get_all_products_with_supplier(self):
        conn = self.get_conn()
        result = conn.execute("""
            SELECT p.id, p.material, p.price_per_unit, p.unit,
                   s.id, s.name, s.company, s.contact, s.latitude, s.longitude
            FROM products p
            JOIN suppliers s ON p.supplier_id = s.id
        """).fetchall()
        conn.close()
        return result

    def delete_product(self, product_id, supplier_id):
        conn = self.get_conn()
        conn.execute(
            "DELETE FROM products WHERE id=? AND supplier_id=?",
            (product_id, supplier_id)
        )
        conn.commit()
        conn.close()

    # ── Buyer methods ────────────────────────────────────────────────────
    def add_buyer(self, telegram_id, name, company):
        conn = self.get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO buyers (telegram_id, name, company) VALUES (?,?,?)",
            (telegram_id, name, company)
        )
        conn.commit()
        conn.close()

    def get_buyer_name(self, telegram_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT name FROM buyers WHERE telegram_id=?", (telegram_id,)
        ).fetchone()
        conn.close()
        return result[0] if result else "Unknown Buyer"

    # ── Order methods ────────────────────────────────────────────────────
    def add_order(self, buyer_telegram_id, buyer_name, supplier_id,
                  supplier_name, product_id, material, quantity, price_per_unit):
        total_cost = round(quantity * price_per_unit, 2)
        commission = round(total_cost * 0.02, 2)
        conn = self.get_conn()
        conn.execute("""
            INSERT INTO orders (buyer_telegram_id, buyer_name, supplier_id, supplier_name,
            product_id, material, quantity, price_per_unit, total_cost, commission)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (buyer_telegram_id, buyer_name, supplier_id, supplier_name,
              product_id, material, quantity, price_per_unit, total_cost, commission))
        conn.commit()
        conn.close()
        return commission, total_cost

    def get_buyer_orders(self, telegram_id):
        conn = self.get_conn()
        result = conn.execute("""
            SELECT id, supplier_name, material, quantity, price_per_unit,
                   total_cost, commission, status, placed_at
            FROM orders WHERE buyer_telegram_id=?
            ORDER BY placed_at DESC
        """, (telegram_id,)).fetchall()
        conn.close()
        return result

    def get_all_orders(self):
        conn = self.get_conn()
        result = conn.execute("""
            SELECT id, buyer_name, supplier_name, material, quantity,
                   total_cost, commission, status, placed_at
            FROM orders ORDER BY placed_at DESC
        """).fetchall()
        conn.close()
        return result

    def get_orders_by_period(self, period="all"):
        conn = self.get_conn()
        if period == "week":
            query = "SELECT * FROM orders WHERE placed_at >= datetime('now', '-7 days') ORDER BY placed_at DESC"
        elif period == "month":
            query = "SELECT * FROM orders WHERE placed_at >= datetime('now', '-30 days') ORDER BY placed_at DESC"
        elif period == "year":
            query = "SELECT * FROM orders WHERE placed_at >= datetime('now', '-365 days') ORDER BY placed_at DESC"
        else:
            query = "SELECT * FROM orders ORDER BY placed_at DESC"
        result = conn.execute(query).fetchall()
        conn.close()
        return result

    # ── Stats methods ────────────────────────────────────────────────────
    def get_stats(self):
        conn = self.get_conn()
        suppliers = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        buyers = conn.execute("SELECT COUNT(*) FROM buyers").fetchone()[0]
        orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0]
        revenue = conn.execute("SELECT SUM(commission) FROM orders").fetchone()[0] or 0
        conn.close()
        return suppliers, buyers, orders, pending, revenue

    def get_revenue_by_period(self, period="all"):
        conn = self.get_conn()
        if period == "week":
            result = conn.execute(
                "SELECT SUM(commission) FROM orders WHERE placed_at >= datetime('now', '-7 days')"
            ).fetchone()[0]
        elif period == "month":
            result = conn.execute(
                "SELECT SUM(commission) FROM orders WHERE placed_at >= datetime('now', '-30 days')"
            ).fetchone()[0]
        elif period == "year":
            result = conn.execute(
                "SELECT SUM(commission) FROM orders WHERE placed_at >= datetime('now', '-365 days')"
            ).fetchone()[0]
        else:
            result = conn.execute("SELECT SUM(commission) FROM orders").fetchone()[0]
        conn.close()
        return result or 0

    def get_total_revenue(self):
        return self.get_revenue_by_period("all")