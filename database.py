import sqlite3

class Database:
    def __init__(self):
        self.db_name = "qurilishlink.db"
        self.init_db()

    def get_conn(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                name TEXT,
                company TEXT,
                material TEXT,
                price_per_unit REAL,
                contact TEXT,
                orders_completed INTEGER DEFAULT 0,
                latitude REAL,
                longtitude REAL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS buyers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                name TEXT,
                company TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_telegram_id INTEGER,
                buyer_name TEXT,
                supplier_id INTEGER,
                supplier_name TEXT,
                material TEXT,
                quantity INTEGER,
                status TEXT DEFAULT 'Pending',
                commission REAL DEFAULT 0,
                placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def add_supplier(self, telegram_id, name, company, material, price, contact, latitude, longtitude):
        conn = self.get_conn()
        conn.execute(
            "INSERT INTO suppliers (telegram_id, name, company, material, price_per_unit, contact, latitude, longtitude) VALUES (?,?,?,?,?,?,?,?)",
            (telegram_id, name, company, material, price, contact, latitude, longtitude)
        )
        conn.commit()
        conn.close()

    def add_buyer(self, telegram_id, name, company):
        conn = self.get_conn()
        conn.execute(
            "INSERT INTO buyers (telegram_id, name, company) VALUES (?,?,?)",
            (telegram_id, name, company)
        )
        conn.commit()
        conn.close()

    def get_all_suppliers(self):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, name, company, material, price_per_unit, contact, orders_completed, latitude, longtitude FROM suppliers"
        ).fetchall()
        conn.close()
        return result

    def get_supplier_by_id(self, supplier_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, name, company, material, price_per_unit, contact FROM suppliers WHERE id=?",
            (supplier_id,)
        ).fetchone()
        conn.close()
        return result

    def add_order(self, buyer_telegram_id, buyer_name, supplier_id, supplier_name, material, quantity, price_per_unit):
        conn = self.get_conn()
        commission = round(quantity * price_per_unit * 0.02, 2)
        conn.execute(
            "INSERT INTO orders (buyer_telegram_id, buyer_name, supplier_id, supplier_name, material, quantity, commission) VALUES (?,?,?,?,?,?,?)",
            (buyer_telegram_id, buyer_name, supplier_id, supplier_name, material, quantity, commission)
        )
        conn.commit()
        conn.close()
        return commission

    def get_buyer_orders(self, telegram_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, supplier_name, material, quantity, status, placed_at FROM orders WHERE buyer_telegram_id=?",
            (telegram_id,)
        ).fetchall()
        conn.close()
        return result

    def get_all_orders(self):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT id, buyer_name, supplier_name, material, quantity, status, placed_at FROM orders"
        ).fetchall()
        conn.close()
        return result

    def get_stats(self):
        conn = self.get_conn()
        suppliers = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        buyers = conn.execute("SELECT COUNT(*) FROM buyers").fetchone()[0]
        orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0]
        conn.close()
        return suppliers, buyers, orders, pending

    def get_buyer_name(self, telegram_id):
        conn = self.get_conn()
        result = conn.execute(
            "SELECT name FROM buyers WHERE telegram_id=?", (telegram_id,)
        ).fetchone()
        conn.close()
        return result[0] if result else "Unknown Buyer"
    
    def get_total_revenue(self):
        conn = self.get_conn()
        result = conn.execute("SELECT SUM(commission) FROM orders").fetchone()[0]
        conn.close()
        return result or 0