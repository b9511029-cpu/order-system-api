# 李品緯(JasonLee)
from datetime import datetime
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from db.database import get_db_connection, DB_PATH, get_db
from main import app
import sqlite3

from routes.order import OrderStatus


@pytest.fixture(autouse=True)
def db_clear():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 409 刪除順序，會受到foreign keys開著，有其他的 Delete 可能會失敗
    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM cart_items")
    cursor.execute("DELETE FROM carts")
    cursor.execute("DELETE FROM menus")
    cursor.execute("DELETE FROM users")

    conn.commit()
    conn.close()
    yield


def setup_db():
    conn = sqlite3.connect(DB_PATH)
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
            description TEXT NOT NULL,
            image_url TEXT 
        )
    """)

    # CREATE TABLE carts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            id TEXT PRIMARY KEY,
            user_id INTEGER UNIQUE,
            updated_at TEXT NOT NULL
        )
    """)

    # CREATE TABLE cart_items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id TEXT PRIMARY KEY,
            cart_id TEXT NOT NULL,
            menu_item_id TEXT NOT NULL,
            quantity INTEGER CHECK(quantity > 0 AND quantity < 20),
            added_at TEXT NOT NULL,
            UNIQUE (cart_id, menu_item_id),
            FOREIGN KEY (cart_id) REFERENCES carts (id) ON DELETE CASCADE
        )
    """)

    # CREATE TABLE order_items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items(
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,

            menu_item_id TEXT NOT NULL,
            menu_name TEXT NOT NULL,

            unit_price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,

            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    """)

    # CREATE TABLE Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            total_amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

setup_db() # 自己建立 test.db all table

def override_get_db():

    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# api 透過 DI(注入) get_db 管理 get_db_connect() 的生命週期
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Cart → Order 的轉換是否成功
def test_checkout_convert_cart_to_order_should_succeed():

    # Arrange user data (資料)
    user_data = {
        "user_id": 1,
        "user_name": "Peter",
        "email": "email@gmail.com",
        "password": "1234566677",
        "created_at":datetime.now().isoformat()
    }
    # Act: 建立使用者
    response_user = client.post("/api/v1/users", json=user_data)

    # Assert: 驗証
    assert response_user.status_code == 201
    data = response_user.json()

    # 取得 user_id
    user_id = data["user_id"]

#-------------------
    # 建立 menu 资料
    # Arrange menu_data (資料)
    menu_data = [
        {"name": "漢堡", "price": 100, "description": "好大顆漢堡",
         "image_url": "https://i.ibb.co/k6Hd5RVm/image.jpg"},
        {"name": "薯條", "price": 50, "description": "一條條",
         "image_url": "https://i.ibb.co/tMDZs0K0/php-Gqw-Cee.jpg"}
    ]

    menu_ids = {} # 装 menu_id

    # Act : 讓 For loop 取 menu_data，變成單筆資料
    for m in menu_data:
        menu_payload = {
            "id": str(uuid4()),
            "name": m["name"],
            "price": m["price"],
            "description": m["description"],
            "image_url": m["image_url"],
        }

        # Act : 請求 API 取得 menu 資料庫資料
        response_menus = client.post("/api/v1/menu", json=menu_payload)
        # Assert API status:
        assert response_menus.status_code == 201
        data = response_menus.json()

        # 建立取 menu_id 的字典结構, 用 data['name'] = data["id"]
        menu_ids[data["name"]] = {"id": data["id"], "price": data["price"]}


        # 取 menu_id value → dict unpacking
    burger_id = menu_ids["漢堡"]["id"]
    burger_price = menu_ids["漢堡"]["price"]

    fries_id = menu_ids["薯條"]["id"]
    fries_price = menu_ids["薯條"]["price"]

    # 計算總金額
    total_amount = (
        burger_price * 2 + fries_price * 1
    )
    assert total_amount == 250
# --------------------------------
    cart_item_id1 = str(uuid4())
    cart_item_id2 = str(uuid4())

    # 建立購物車商品
    response_item1 = client.post(f"/api/v1/cart/{user_id}/items", json={
        "id": cart_item_id1,
        "menu_item_id": burger_id,
        "quantity": 2
    }) # 建立第一個商品
    # Assert 1st 商品
    assert response_item1.status_code == 201
    # print("item1",item1)

    response_item2 = client.post(f"/api/v1/cart/{user_id}/items", json={
        "id": cart_item_id2,
        "menu_item_id": fries_id,
        "quantity": 1
    }) # 建立第二個商品
    # Assert 2nd 商品
    assert response_item2.status_code == 201
    # print("item2",response_item2.json())


    # 建立 Order ,
    order_payload = {
        "id": str(uuid4()),
        "user_id": user_id,
        "total_amount": total_amount,
        "status": OrderStatus.pending,
        "created_at": datetime.now().isoformat(),
        "items":[]
    }

    response_order = client.post(f"/api/v1/order/",json=order_payload)

    assert response_order.status_code == 201, response_order.text
    print(response_order.text)
    print(response_order.json())
    print(response_order.status_code)
    order_response = response_order.json()
    print("HEADERS:", response_order.headers)
    assert order_response["user_id"] == user_id
    assert order_response["total_amount"] == 250
    assert order_response["status"] == "pending"

    assert len(order_response["items"]) == 2

    response_cart = client.get(f"/api/v1/cart/{user_id}")

    cart = response_cart.json()

    assert cart["items"] == []



























