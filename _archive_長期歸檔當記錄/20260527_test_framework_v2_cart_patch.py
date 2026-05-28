# 李品緯(JasonLee)
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient
from API作品.app.cart import app, get_db
from API作品.db.database import DB_PATH


#----------------------------------------
# 建立測試用的連線，透過DB_PATH 連線到 Test.db
#----------------------------------------
def override_get_db():
    conn = sqlite3.connect(DB_PATH)
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

    # Carts
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                id TEXT PRIMARY KEY,
                user_id INTEGER UNIQUE,
                updated_at TEXT NOT NULL
            )
    """)

    # Cart_items
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id TEXT PRIMARY KEY,
                cart_id TEXT NOT NULL,
                menu_item_id TEXT NOT NULL,
                quantity INTEGER,
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

    cursor.execute("DELETE FROM cart_items")
    cursor.execute("DELETE FROM carts")

    conn.commit()
    conn.close()

    yield

#---------------------
# Arrange (測試資料)
#---------------------
def seed_cart_with_item():
    user_id = 2
    cart_id = str(uuid4())
    cart_item_id = str(uuid4())
    menu_item_id = str(uuid4())
    now = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Taipei")).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO carts VALUES (?,?,?)",
                   (cart_id, user_id, now))

    cursor.execute("INSERT INTO cart_items VALUES (?,?,?,?,?)",
                   (cart_item_id, cart_id, menu_item_id, 3, now))

    conn.commit()
    conn.close()

    return cart_id, user_id, menu_item_id


#--------------------------------------
# FastAPI 正式環境DB 替換 測試用的 Test.db
#--------------------------------------
app.dependency_overrides[get_db] = override_get_db

#-------------------------
# Test FastAPI
#-------------------------
client = TestClient(app)


# SQLite + API test
#--------------------------------------------------------------
# update (Patch) Test
#--------------------------------------------------------------
def test_patch_cart_item_should_update_quantity():
    # Given: Arrange (準備資料)
    cart_id, user_id, menu_item_id = seed_cart_with_item()

    payload = {
        "quantity": 5
    }
    # When: Act (呼叫API)
    res = client.patch(f"/api/v2/cart/{user_id}/items/{menu_item_id}",
                       json=payload)

    # Then: Assert (驗證結果)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == user_id
    assert "cart_id" in data
    assert "updated_at" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 5

def test_patch_cart_item_should_delete_when_quantity_zero():
    # Given: Arrange (準備資料)
    cart_id, user_id, menu_item_id = seed_cart_with_item()

    payload = {
        "quantity": 0
    }

    # When: Act (呼叫 API)
    res = client.patch(f"/api/v2/cart/{user_id}/items/{menu_item_id}",
                       json=payload)

    # Then: Assert (驗證結果)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0


def test_patch_cart_item_not_found_should_fail():
    # Given: Arrange (準備資料)
    cart_id, user_id, menu_item_id = seed_cart_with_item()

    fake_menu_item_id = str(uuid4()) # 不存在 Item

    payload = {
        "quantity": 5
    }

    # When: Act (呼叫 API)
    res = client.patch(f"/api/v2/cart/{user_id}/items/{fake_menu_item_id}",
                       json=payload)

    # Then: Assert (驗證錯誤)
    assert res.status_code == 404
    data = res.json()
    assert data["detail"] == "cart items not found"

def test_patch_cart_not_found_should_fail():
    # Given: Arrange (無準備資料)
    menu_item_id = str(uuid4())
    fake_user_id = 999

    payload = {
        "quantity": 5
    }
    # When: Act (呼叫 API)
    res = client.patch(f"/api/v2/cart/{fake_user_id}/items/{menu_item_id}",
                       json=payload)
    # Then: Assert (驗證錯誤)
    assert res.status_code == 404
    data = res.json()
    assert data["detail"] == "cart not found"

def test_patch_cart_item_greater_than_20_should_fail():
    # Given: Arrange (準備資料)
    cart_id, user_id, menu_item_id = seed_cart_with_item()
    payload = {
        "quantity": 23
    }
    # When: Act (呼叫 API)
    res = client.patch(f"/api/v2/cart/{user_id}/items/{menu_item_id}",
                       json=payload)
    # Then: Assert (驗證錯誤)
    assert res.status_code == 400
    data = res.json()
    assert data["detail"] == "quantity cannot be greater than 20"

def test_patch_cart_item_quantity_negative_should_fail():
    # Given: Arrange (準備資料)
    cart_id, user_id, menu_item_id = seed_cart_with_item()
    payload = {
        "quantity": -4
    }
    # When: Act (呼叫 API)
    res = client.patch(f"/api/v2/cart/{user_id}/items/{menu_item_id}",
                       json=payload)
    # Then: Assert (驗證錯誤)
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data




















