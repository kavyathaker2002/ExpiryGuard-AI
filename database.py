import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from flask import g, current_app

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    db_path = app.config['DATABASE']
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                preferred_language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Products table (exact 6 fields + metadata)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                brand TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                package_size TEXT NOT NULL DEFAULT '',
                mfg_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                barcode TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE (user_id, barcode)
            )
        """)

        # Safe additive migration for databases created by earlier versions.
        product_columns = {row[1] for row in cursor.execute("PRAGMA table_info(products)").fetchall()}
        for column in ('brand', 'category', 'package_size'):
            if column not in product_columns:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")

        # 3. Sales table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                quantity_sold INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_amount REAL NOT NULL,
                sale_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_user ON products(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_barcode ON products(user_id, barcode);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_expiry ON products(expiry_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_user ON sales(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_timestamp ON sales(sale_timestamp);")
        
        # Check if default admin user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ('admin',))
        admin_user = cursor.fetchone()
        if not admin_user:
            cursor.execute(
                "INSERT INTO users (shop_name, username, password_hash, preferred_language) VALUES (?, ?, ?, ?)",
                ("Gupta Chaat & Stores", "admin", generate_password_hash("admin 123"), "en")
            )
            admin_user_id = cursor.lastrowid
            seed_demo_inventory(cursor, admin_user_id)
            
        # Also clean up any legacy demo_shop user if present
        cursor.execute("DELETE FROM users WHERE username = 'demo_shop'")
            
        conn.commit()

def seed_demo_inventory(cursor, user_id):
    """Seed realistic Kirana store items with different expiry stages for demonstration"""
    today = datetime.now()
    
    # helper for dates YYYY-MM-DD
    def d_str(dt):
        return dt.strftime('%Y-%m-%d')
    
    demo_products = [
        # (Name, Mfg offset days, Exp offset days, Barcode, Qty, Price)
        ("Amul Taaza Milk 500ml", -3, 2, "8901262010053", 14, 27.0),       # Expires in 2 days (Critical)
        ("Britannia 100% Whole Wheat Bread", -4, 4, "8901063102123", 8, 45.0), # Expires in 4 days (Critical)
        ("Mother Dairy Paneer 200g", -8, 6, "8901648001019", 12, 90.0),      # Expires in 6 days (Critical)
        ("Epigamia Greek Yogurt 90g", -15, 11, "8908006371028", 15, 50.0),    # Expires in 11 days (Urgent)
        ("Harvest Gold Burger Buns", -3, 14, "8906012430041", 6, 35.0),       # Expires in 14 days (Urgent)
        ("Parle-G Gold Biscuits 1kg", -60, 22, "8901719101015", 25, 120.0),   # Expires in 22 days (Warning)
        ("Britannia Good Day Butter 250g", -90, 28, "8901063011128", 30, 40.0),# Expires in 28 days (Warning)
        ("Haldiram Nagpur Aloo Bhujia 400g", -120, -5, "8904004400124", 4, 95.0), # Expired 5 days ago (Expired!)
        ("Maggi 2-Minute Masala Noodles 280g", -90, 180, "8901058852415", 50, 48.0), # Safe (180 days)
        ("Tata Salt Iodized 1kg", -180, 540, "8904043901006", 40, 28.0),     # Safe (540 days)
        ("Aashirvaad Superior MP Sharbati Atta 5kg", -30, 150, "8901725131012", 18, 310.0), # Safe
        ("Fortune Sunlite Sunflower Oil 1L", -45, 270, "8906007280019", 22, 145.0), # Safe
        ("Cadbury Dairy Milk Silk 60g", -30, 120, "7622201443213", 2, 85.0),  # Low Stock (2 units)
    ]
    
    for name, mfg_off, exp_off, barcode, qty, price in demo_products:
        mfg = d_str(today + timedelta(days=mfg_off))
        exp = d_str(today + timedelta(days=exp_off))
        cursor.execute("""
            INSERT OR IGNORE INTO products (user_id, product_name, mfg_date, expiry_date, barcode, quantity, price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, mfg, exp, barcode, qty, price))
        
        prod_id = cursor.lastrowid
        # Seed some initial historical sales for the ML predictor and charts
        if prod_id:
            # Add sales in past 7 days
            for past_day in range(1, 8):
                sale_time = (today - timedelta(days=past_day, hours=past_day * 2)).strftime('%Y-%m-%d %H:%M:%S')
                sold_qty = (prod_id % 3) + 1
                cursor.execute("""
                    INSERT INTO sales (product_id, user_id, quantity_sold, unit_price, total_amount, sale_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (prod_id, user_id, sold_qty, price, sold_qty * price, sale_time))
