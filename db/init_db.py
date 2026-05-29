# 李品緯(JasonLee)
import sqlite3

conn = sqlite3.connect("app.db")

conn.execute("PRAGMA foreign_keys = ON") # 設計外鍵ON，是為了保護資料完整性

cursor = conn.cursor()

# CREATE TABLE users
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
        )
""")

# CREATE TABLE menu
cursor.execute("""
    CREATE TABLE IF NOT EXISTS menus (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        description TEXT,
        image_url TEXT
        )
""")

# CREATE TABLE cart_items
cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart_items (
        id TEXT PRIMARY KEY,
        cart_id INTEGER NOT NULL, 
        menu_item_id TEXT NOT NULL,
        quantity INTEGER,
        added_at TEXT NOT NULL,
        UNIQUE (cart_id, menu_item_id),
        FOREIGN KEY (cart_id) REFERENCES carts (id) ON DELETE CASCADE
        )
""")

# CREATE TABLE carts
cursor.execute("""
    CREATE TABLE IF NOT EXISTS carts (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL, 
        updated_at TEXT NOT NULL
        )
""")

conn.commit()
conn.close()