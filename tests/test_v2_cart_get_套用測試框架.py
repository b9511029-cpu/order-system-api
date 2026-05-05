# 李品緯(JasonLee)
import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from API作品.app.cart_api_main import app, get_db, DB_PATH

#-----------------
# 連線到 test.db
#-----------------
def override_get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
#---------------------
# 建立測試資料庫的資料表
#---------------------
@pytest.fixture(autouse=True)  # 建 test_cart.db conn
def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 建表 (最小版本)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id TEXT PRIMARY KEY,
            cart_id TEXT,
            menu_item_id TEXT,
            quantity INTEGER
            added_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close() # test end close



# ------------------------------
# Clean DB
# ------------------------------
@pytest.fixture(autouse=True)
def clean_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM carts")
    cursor.execute("DELETE FROM cart_items")

    conn.commit()
    conn.close()

# 將正式用的db 更換成測試用db
app.dependency_overrides[get_db] = override_get_db


# --------------
# 呼叫API
# --------------
client = TestClient(app)


#-------------------------------------------------
# Arrange data (準備資料) --> DB card and CartItem
#-------------------------------------------------
def seed_cart_with_items():
    user_id = 1
    cart_id = str(uuid4())
    cart_item_id= str(uuid4())
    menu_item_id = str(uuid4())
    now = (datetime.now(timezone.utc)
           .astimezone(ZoneInfo("Asia/Taipei"))
           .isoformat())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 插入cart資料
    cursor.execute("INSERT INTO carts(id, user_id, updated_at) VALUES(?,?,?)",
                   (cart_id,user_id,now))

    # 插入items 資料
    cursor.execute("""INSERT INTO cart_items(id, cart_id, menu_item_id, quantity, added_at) 
                          VALUES(?,?,?,?,?)""",
                   (cart_item_id, cart_id, menu_item_id, 3, now))

    conn.commit()
    conn.close()

    return cart_id,user_id

def seed_cart_not_with_items():
    user_id = 2
    cart_id = str(uuid4())
    now = (datetime.now(timezone.utc)
           .astimezone(ZoneInfo("Asia/Taipei"))
           .isoformat())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO carts(id, user_id, updated_at) VALUES(?,?,?)"
                   ,(cart_id, user_id, now))

    # 沒有 CartItem

    conn.commit()
    conn.close()

    return cart_id,user_id # (tuple)

#--------------------
# 測試程式
#--------------------
def test_get_cart_should_return_items():
    # Given: Arrange (準備資料)
    cart_id,user_id = seed_cart_with_items()

    # When: Act (呼叫API)
    res = client.get(f"/api/v2/cart/{user_id}")

    # Then: Assert (驗證結果)
    assert res.status_code == 200

    # Cart level 內部資料
    data = res.json()
    assert data['user_id'] == user_id
    assert data['cart_id'] == cart_id
    assert data['updated_at'] is not None

    # Cart_Items level
    assert len(data['items']) == 1
    assert data['items'][0]['menu_item_id'] is not None
    assert data['items'][0]['quantity'] == 3


def test_get_cart_should_return_empty_items():
    # Given: Arrange (準備資料)
    cart_id, user_id = seed_cart_not_with_items() # tuple unpacking
    # When:  Act (呼叫 API)
    res = client.get(f"/api/v2/cart/{user_id}")
    # Then:  Assert (驗證結果)
    assert res.status_code == 200
    data = res.json()
    # 驗證 Cart 內部資料
    assert data["user_id"] == user_id
    assert data["cart_id"] == cart_id
    assert data["updated_at"] is not None
    # 驗證 CartItem = empty
    assert data["items"] == []
    assert isinstance(data["items"],list) # 順便驗證型別


def test_get_cart_not_found_should_fail():
    # Given: Arrange (DB 空的 , 沒有 Cart)
    user_id = 999
    # When: 呼叫 (API)
    res = client.get(f"/api/v2/cart/{user_id}")
    # Then: Assert 驗證錯誤 404
    assert res.status_code == 404
    data = res.json()
    assert data["detail"] == "cart not found"
    assert "user_id" not in data



