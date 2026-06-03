# 李品緯(JasonLee)
import sqlite3
import zoneinfo
from datetime import datetime, timezone
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from API作品.app.cart import router, get_db
from API作品.db.database import DB_PATH, get_db_connection


#----------------------------------------
# 建立測試用的連線，透過DB_PATH 連線到 Test.db
#----------------------------------------
def override_get_db():
    # conn = sqlite3.connect(DB_PATH)
    conn = get_db_connection()
    try:
        yield conn

    finally:
        conn.close()

#---------------------
# 建立測試資料庫的資料表
#---------------------
@pytest.fixture(autouse=True)
def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
            )
    """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                    id TEXT PRIMARY KEY,
                    cart_id TEXT NOT NULL,
                    menu_item_id TEXT NOT NULL,
                    quantity INTEGER 
                    added_at TEXT NOT NULL,
                    UNIQUE (cart_id, menu_item_id),
                    FOREIGN KEY (cart_id) REFERENCES carts (id) ON DELETE CASCADE
            )
    """)

    conn.commit()
    conn.close()

#---------------------
# SQLite DB clear
#---------------------
@pytest.fixture(autouse=True)
def db_clear():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM carts")
    cursor.execute("DELETE FROM cart_items")

    conn.commit()
    conn.close()

    yield

#---------------------
# Arrange (準備資料)
#---------------------
def seed_cart_with_item():
    user_id = 3
    cart_id = str(uuid4())
    cart_item_id = str(uuid4())
    menu_item_id = str(uuid4())
    new_taipei = (datetime.now(timezone.utc)
                  .astimezone(zoneinfo.ZoneInfo("Asia/Taipei"))
                  .isoformat())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO carts VALUES (?,?,?)",
                   (cart_id, user_id, new_taipei))

    cursor.execute("INSERT INTO cart_items VALUES (?,?,?,?,?)",
                   (cart_item_id, cart_id, menu_item_id, 5, new_taipei))

    conn.commit()
    conn.close()

    return cart_id, user_id, menu_item_id

#--------------------------------------
# FastAPI 正式環境DB 替換 測試用的 Test.db
#--------------------------------------
router.dependency_overrides[get_db] = override_get_db


#-------------------------
# Test FastAPI
#-------------------------
client = TestClient(router)


def test_delete_cart_item_should_succeed():
    # Given: Arrange (準備資料)
    cart_id, user_id, menu_item_id = seed_cart_with_item()

    # When: Act (呼叫API)
    res = client.delete(f"/api/v2/cart/{user_id}/items/{menu_item_id}")

    # Then: Assert (驗證結果)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == user_id
    assert data["cart_id"] == cart_id
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0
    assert len(data["updated_at"]) > 0


    # 資料庫已刪除 item
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cart_items WHERE cart_id = ?",
                   (cart_id,))
    rows = cursor.fetchall()
    assert len(rows) == 0


def test_delete_cart_not_found_should_fail():
    # Given: Arrange(準備資料)
    user_id = 999
    menu_item_id = str(uuid4())

    # When: Act (呼叫API)
    res = client.delete(f"/api/v2/cart/{user_id}/items/{menu_item_id}")

    # Then: Assert (驗證 cart 錯誤)
    assert res.status_code == 404
    data = res.json()
    assert data["detail"] == "cart not found"
    assert "detail" in data


def test_delete_cart_item_not_found_should_fail():
    # Given: Arrange (準備資料)
    cart_id, user_id, menu_item_id = seed_cart_with_item()
    fake_menu_item_id = str(uuid4())

    # When: Act (呼叫API)
    res = client.delete(f"/api/v2/cart/{user_id}/items/{fake_menu_item_id}")

    # Then: Assert (驗證 item 錯誤)
    assert res.status_code == 404
    data = res.json()
    assert data
    assert data["detail"] == "item not found"
    assert "detail" in data
    # 驗證 DB 購物車還存在 沒被誤刪
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM carts WHERE user_id = ?",
                       (user_id,))
        # 語意明確
        cart_count = cursor.fetchone()[0]
        assert cart_count == 1,"cart should still exist"


