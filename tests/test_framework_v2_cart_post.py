# 李品緯(JasonLee)
import sqlite3
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from API作品.routes.cart import router,get_db
from API作品.db.database import DB_PATH, get_db_connection


#----------------------------
# Connect test.db
#----------------------------
def override_get_db():
    # conn = sqlite3.connect(DB_PATH)　,不使用手寫 conn.row_factory，是因為怕會散落在各處
    conn = get_db_connection() # 使用database.py.get_db_connect()，就是為了統一管理連線部分，這樣可以減少重覆與遺忘
    try:
        yield conn
    finally:
        conn.close()

#----------------------------
# 建立測試資料庫的資料表
#----------------------------
def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts(
                id TEXT PRIMARY KEY,
                user_id INTEGER UNIQUE,
                updated_at TEXT NOT NULL
            )
    """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart_items(
                id TEXT PRIMARY KEY,
                cart_id TEXT NOT NULL,
                menu_item_id TEXT NOT NULL,
                quantity INTEGER CHECK(quantity > 0 AND quantity <= 20)
                added_at TEXT NOT NULL,
                UNIQUE (cart_id, menu_item_id),
                FOREIGN KEY (cart_id) REFERENCES carts (id) ON DELETE CASCADE
            )
    """)
    conn.commit()
    conn.close()

#--------------------------------------------------------------
# SQLite DB clear
#--------------------------------------------------------------
@pytest.fixture(autouse=True)
def db_clear():
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart_items")

    conn.commit()
    conn.close()

    yield

#-------------------------------------------------
# 告訴 API 不要走正式環境 DB ,我有提供一個測試用DB給你測試
# override_get_db -> DB PATH -> 替換過的 test.db
#-------------------------------------------------
router.dependency_overrides[get_db] = override_get_db

client = TestClient(router)

# SQLite + API test
#--------------------------------------------------------------
# Create Cart Test
#--------------------------------------------------------------
def test_add_new_cart():
    user_id = 1
    menu_item_id = str(uuid4())
    # 呼叫API
    res1 = client.post(f"/api/v2/cart/{user_id}/items",
                json={
                    "menu_item_id": menu_item_id,
                    "quantity": 3,
                    }
    )
    # 驗證 狀態碼
    assert res1.status_code == 201
    # # 查DB (是否有建立第一筆購物車)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 查購物車內容
    cursor.execute("""SELECT * FROM carts WHERE user_id = ?
                   """,(user_id,)
                   )
    carts = cursor.fetchall() # 拿到資料

    # 查購物車商品
    cursor.execute("SELECT * FROM cart_items")
    cart_item = cursor.fetchall()

    conn.close() # 關閉連線
    # assert
    assert len(carts) == 1
    assert len(cart_item) == 1
    assert cart_item[0][1] == carts[0][0]
    assert cart_item[0][3] == 3

def test_add_same_item():
    user_id = 2
    menu_item_id = str(uuid4()) # 使用同一個購物車商品編號
    client.post(f"/api/v2/cart/{user_id}/items",
                json={
                    "menu_item_id": menu_item_id,
                    "quantity": 3
                }
    )
    res = client.post(f"/api/v2/cart/{user_id}/items",
                       json={
                           "menu_item_id": menu_item_id,
                           "quantity": 4
                       }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user_id"] == 2
    assert "cart_id" in data
    assert len(data["items"]) == 1 # 驗證只有一筆商品資料
    # 使用內部驗證 next():從 list 裡面找到第一個符合條件的元素
    item = next(i for i in data["items"] if i["menu_item_id"] == menu_item_id)
    assert item["quantity"] == 7

def test_add_different_items():
    user_id = 3
    item1 = str(uuid4())
    item2 = str(uuid4())
    client.post(f"/api/v2/cart/{user_id}/items",
                json={
                    "menu_item_id": item1,
                    "quantity": 3
                })

    res = client.post(f"/api/v2/cart/{user_id}/items",
                json={
                    "menu_item_id": item2,
                    "quantity": 4
                })
    assert res.status_code == 201
    data = res.json()
    # 兩筆商品資料
    assert len(data["items"]) == 2
    # 分別驗證 (字典推導式) 需要一次性讀取多筆資料驗證情況
    item_map = {i["menu_item_id"]: i for i in data["items"]}
    assert item_map[item1]['quantity'] == 3
    assert item_map[item2]['quantity'] == 4

#----------------------------------------------------
# Validation Beyond(邊界) Test
#----------------------------------------------------
def test_add_item_with_min_quantity_should_succeed():
    # Given: 新增使用者與商品
    user_id = 4
    menu_item_id = str(uuid4())

    # When: 加入 quantity = 1
    res = client.post(f"/api/v2/cart/{user_id}/items",
                json={
                    'menu_item_id': menu_item_id,
                    'quantity': 1
                }
    )
    # Then: 回傳成功
    assert res.status_code == 201
    data = res.json()
    assert len(data["items"]) == 1
    # 改成用條件查找確保驗證的是正確商品，不依賴 list 順序性
    # assert data["items"][0]["quantity"] == 1
    item = next(i for i in data["items"] if i["menu_item_id"] == menu_item_id)
    assert item["quantity"] == 1

def test_add_item_with_max_quantity_should_succeed():
    # Given: 新使用者與商品
    user_id = 5
    menu_item_id = str(uuid4())
    # When 加入 quantity = 20
    res = client.post(f"/api/v2/cart/{user_id}/items",
                       json={
                           'menu_item_id': menu_item_id,
                           'quantity':20
                       }
    )
    # Then: 回傳成功
    assert res.status_code == 201
    data = res.json()
    assert len(data["items"]) == 1
    item = next(i for i in data["items"] if i["menu_item_id"] == menu_item_id)
    assert item["quantity"] == 20

def test_add_item_with_quantity_zero_should_fail():
    # Given: 新增使用者與商品
    user_id = 6
    menu_item_id = str(uuid4())

    # When: 加入 quantity = 0
    res = client.post(f"/api/v2/cart/{user_id}/items",
                json={
                    "menu_item_id": menu_item_id,
                    "quantity": 0
                }
    )
    # Then: 回傳驗證錯誤
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "greater than" in data["detail"][0]["msg"]

def test_add_item_with_quantity_21_should_fail():
    # Given: 新增使用者與商品
    user_id = 7
    menu_item_id = str(uuid4())

    # When: 加入 quantity = 21
    res = client.post(f"/api/v2/cart/{user_id}/items",
                         json={
                            'menu_item_id': menu_item_id,
                             "quantity": 21
                         }
    )
    # Then: 回傳驗證錯誤
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "less than or equal" in data["detail"][0]['msg']

# 非法輸入測試
def test_add_item_with_negative_quantity_should_fail():
    # Given: 新增使用者與商品
    user_id = 8
    menu_item_id = str(uuid4())

    # When: 加入 quantity = -1
    res = client.post(f"/api/v2/cart/{user_id}/items",
                          json={
                            "menu_item_id": menu_item_id,
                            "quantity": -1
                          }
    )
    # Then: 回傳驗證錯誤
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "greater than" in data["detail"][0]['msg']

#----------------------------------------------------
# Invalid Input Test
#----------------------------------------------------

def test_add_item_with_str_quantity_should_fail():
    # Given: 新增使用者與商品
    user_id = 9
    menu_item_id = str(uuid4())

    # When: 傳入非數字 quantity (string)
    res = client.post(f"/api/v2/cart/{user_id}/items",
                          json={
                            "menu_item_id": menu_item_id,
                            "quantity": "string"
                          }
    )
    # Then 回傳驗證錯誤
    assert res.status_code == 422
    data = res.json()

    assert "detail" in data
    assert "integer" in data["detail"][0]['msg']

    # When:
def test_add_item_with_none_quantity_should_fail():
    # Given: 新增使用者與商品
    user_id = 10
    menu_item_id = str(uuid4())

    # When: 傳入非合法 quantity (None)
    res = client.post(f"/api/v2/cart/{user_id}/items",
                           json={
                            "menu_item_id": menu_item_id,
                            "quantity": None
                           }
    )

    # Then: 回傳驗證錯誤
    assert res.status_code == 422
    data = res.json()

    assert "detail" in data
    assert "integer" in data["detail"][0]["msg"]

def test_add_item_with_missing_field_should_fail():
    # Given: 新增使用者與商品
    user_id = 11
    menu_item_id = str(uuid4())
    # When: 沒有傳入 quantity field
    res = client.post(f"/api/v2/cart/{user_id}/items",
                      json={
                        "menu_item_id":menu_item_id
                      }
    )
    # Then: 回傳驗證錯誤
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "required" in data["detail"][0]["msg"].lower()
    # .lower() ->python 字串方法 把字串全部轉成小寫（lowercase）


def test_add_item_with_invalid_uuid_should_fail():
    # Given: 新增使用者與商品
    user_id = 12
    # When: 傳入 request field not is uuid
    res = client.post(f"/api/v2/cart/{user_id}/items",
                      json={
                        "menu_item_id": "not a uuid",
                        "quantity": 3
                      }
    )
    # 回傳驗證錯誤
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "uuid" in data["detail"][0]["type"]


def test_add_item_empty_payload_should_fail():
    # Given: 新增使用者
    user_id = 13
    # When: 傳入 Empty Payload
    res = client.post(f"/api/v2/cart/{user_id}/items",
                      json={})
    # 回傳驗證錯誤
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "missing" in data["detail"][0]["type"]
    assert len(data["detail"]) >= 1


#----------------------------------------------------
# Business Logic Test
#----------------------------------------------------
def test_add_same_item_with_accumulation_exceeding_max_quantity_should_fail():
    # Given: 新增使用者與商品
    user_id = 11
    menu_item_id = str(uuid4())

    # When: 第一次加入
    res_1 = client.post(f"/api/v2/cart/{user_id}/items",
                json={
                    "menu_item_id": menu_item_id,
                    "quantity": 15
                }
    )
    assert res_1.status_code == 201

    # When: 第二次加入
    res_2= client.post(f"/api/v2/cart/{user_id}/items",
                      json={
                        "menu_item_id": menu_item_id,
                        "quantity": 6
                      }
    )
    # Then: 回傳業務邏輯錯誤
    assert res_2.status_code == 400 # Bad request (符合業務邏輯錯誤)
    data = res_2.json()
    assert "detail" in data
    assert "cannot exceed" in data["detail"]























