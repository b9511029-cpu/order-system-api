# 李品緯(JasonLee)
# .pytest 測試起來更直覺、清晰、第三方套件、進行參數化測試(方便簡單)
import sqlite3
from uuid import uuid4
from API作品.routes.menu import router
from fastapi.testclient import TestClient
from API作品.db.database import DB_PATH

client = TestClient(router)

def clear_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menus")
    conn.commit()
    conn.close()

# -----------------
# Create Menu Test
# -----------------

def test_create_meal_should_succeed():
    clear_db()
    # Given: 新增商品
    menu_id = str(uuid4())
    payload = {
        'id': menu_id,
        'name': '牛肉麵',
        'price': 120,
        'description': '經典紅燒牛肉麵',
        'image_url': 'https://example.com/beef.jpg'
    }
    # When 加入餐點
    response = client.post("/api/v1/menu",json=payload)

    # Then: 回傳成功
    assert response.status_code in (200,201)
    data = response.json()
    assert data['id'] == menu_id
    assert data['name'] == '牛肉麵'
    assert data['price'] == 120
    assert data['description'] == '經典紅燒牛肉麵'
    assert data['image_url'] == 'https://example.com/beef.jpg'

#----------------
# Duplicate test
#----------------
def test_create_meal_duplicate_should_fail():
    clear_db()
    # Given: 新增商品
    menu_id = str(uuid4())
    payload = {
        'id': menu_id,
        'name': '牛肉麵',
        'price': 120,
        'description': '經典紅燒牛肉麵',
        'image_url': 'https://example.com/beef.jpg'
    }
    # When: 加入第一筆餐點
    response1 = client.post("/api/v1/menu",json=payload)
    assert response1.status_code == 201
    # When: 加入第二筆餐點
    response2 = client.post("/api/v1/menu",json=payload)

    # Then: 回傳驗證錯誤
    assert response2.status_code == 409
    data = response2.json()
    assert data['detail'] == "ID already exists"


#----------------
# Get All Menu Test
#----------------
def test_get_all_meals_should_succeed():
    clear_db()
    # Given: 新增商品
    menu_id = str(uuid4())
    payload = {
        'id': menu_id,
        'name': '牛肉麵',
        'price': 120,
        'description': '經典紅燒牛肉麵',
        'image_url': 'https://example.com/beef.jpg'
    }
    # When: 加入第一筆餐點
    data = client.post("/api/v1/menu",json=payload)
    # When: 查詢結果
    response = client.get("/api/v1/menu")
    # Then: 回傳成功
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data,list)
    assert len(data) == 1
    assert data[0]['id'] == menu_id

#----------------
# Get Menu Test
#----------------

def test_get_single_meal_should_success():
    clear_db()
    # Given: 新增商品
    menu_id = str(uuid4())
    payload = {
        "id": menu_id,
        "name": "Burger",
        "price": 100,
        "description": "Beef burger",
        "image_url": None
    }
    # When: 加入第一個餐點
    client.post("/api/v1/menu/",json=payload)
    # When: 查詢一個餐點
    response = client.get(f"/api/v1/menu/{menu_id}")

    # Then: 回傳成功
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == menu_id
    assert data["name"] == "Burger"
    assert data["price"] == 100
    assert data["description"] == "Beef burger"
    assert data["image_url"] is None


# -----------------------
# Update Menu Test (PUT)
# -----------------------
def test_update_all_menu_item_should_succeed():
    clear_db()
    # Given: 新增商品
    menu_id = str(uuid4())
    payload = {
        'id': menu_id,
        'name': '牛肉麵',
        'price': 120,
        'description': '經典紅燒牛肉麵',
        'image_url': 'https://example.com/beef.jpg'
    }

    # When: 加入第一筆新增
    client.post("/api/v1/menu/",json=payload)

    # When: 加入更新資料
    update = {
        'id': menu_id,
        'name': '番茄牛肉麵',
        'price': 200,
        'description': '酸甜可口，香味四溢',
        'image_url': 'https://example.com/beef.jpg'
    }
    response = client.put(f"/api/v1/menu/{menu_id}",json=update)
    # Then: 回傳成功
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == '番茄牛肉麵'
    assert data['price'] == 200
    assert data['description'] == '酸甜可口，香味四溢'
    assert data['image_url'] == 'https://example.com/beef.jpg'


def test_update_menu_item_not_found_should_fail():
    # 當資料庫沒有資料，會先驗證資料庫，所以回應就會是404
    clear_db()
    # Given:新增商品
    menu_id = str(uuid4())
    payload = {
        'id': menu_id,
        'name': '番茄牛肉麵',
        'price': 200,
        'description': '酸甜可口，香味四溢',
        'image_url': 'https://example.com/beef.jpg'
    }
    # When: DB 沒有目前餐點紀錄
    # When: 更新餐點Items
    response = client.put(f"/api/v1/menu/{menu_id}",json=payload)
    # Then: 回傳錯誤
    assert response.status_code ==404
    data = response.json()
    assert data['detail'] == "Item not found"


def test_update_menu_item_id_not_match_should_fail():
    clear_db()
    # Given:新增商品和更新商品
    menu_id_1 = str(uuid4())
    menu_id_2 = str(uuid4())
    payload_1 ={
        'id': menu_id_1,
        'name': '牛肉麵',
        'price': 120,
        'description': '經典紅燒牛肉麵',
        'image_url': 'https://example.com/beef.jpg'
    }
    payload_2 ={
        'id': menu_id_2,
        'name': '番茄牛肉麵',
        'price': 200,
        'description': '酸甜可口，香味四溢',
        'image_url': 'https://example.com/beef.jpg'
    }
    # When: 加入第一筆餐點
    client.post(f"/api/v1/menu/{menu_id_1}",json=payload_1)

    # When: 更新時,餐點編號不一致
    response = client.put(f"/api/v1/menu/{menu_id_1}",json=payload_2)

    # Then: 回傳錯誤
    assert response.status_code == 400
    data = response.json()
    assert data['detail'] == "item_id 與 item.id 不匹配"
    print('測試成功:更新失敗(PUT)')

# --------------------------------------------------------------
# Update Menu Test (PATCH)
# --------------------------------------------------------------
def test_patch_menu_item_should_succeed():
    clear_db()
    # Given: 新增商品
    menu_id_1 = str(uuid4())
    # When: 新增第一筆餐點
    res = client.post("/api/v1/menu/",
                json={
                    'id':menu_id_1,
                    'name': '牛肉麵',
                    'price': 120,
                    'description': '經典紅燒牛肉麵',
                    'image_url': 'https://example.com/beef.jpg'
                }
    )
    assert res.status_code == 201
    data = res.json()
    assert data['id'] == menu_id_1
    assert data['price'] == 120

    # When: 傳入修改價格 price = 300
    response = client.patch(f"/api/v1/menu/{menu_id_1}",
                            json={'price': 300}
                            )

    # Then: 回傳更新價格成功
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == menu_id_1
    assert data['name'] == '牛肉麵'
    assert data['price'] == 300
    assert data['description'] == '經典紅燒牛肉麵'
    assert data['image_url'] == 'https://example.com/beef.jpg'


def test_patch_menu_item_not_found_source_should_fail():
    clear_db()
    # Given: 新增商品
    menu_id_1 = str(uuid4())
    menu_id_2 = str(uuid4())
    # When: 加入一筆餐點
    res = client.post("/api/v1/menu/",
                json={
                    'id': menu_id_1,
                    'name': '牛肉麵',
                    'price': 120,
                    'description': '經典紅燒牛肉麵',
                    'image_url': 'https://example.com/beef.jpg'
                }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["id"] == menu_id_1
    # When: 資料不存在
    response = client.patch(f"/api/v1/menu/{menu_id_2}",
                            json={'price': 300,}
                            )
    # Then: 回傳錯誤
    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == "Item not found"


def test_patch_menu_item_request_not_found_should_fail():
    clear_db()
    # Given: 新增商品
    menu_id_1 = str(uuid4())

    # When: 加入一筆餐點
    res = client.post("/api/v1/menu",
                      json={
                          'id': menu_id_1,
                          'name': '乾麵',
                          'price': 60,
                          'description': '順滑爽口',
                          'image_url': 'https://example.com/beef.jpg'
                      }
    )
    assert res.status_code == 201
    data1 = res.json()
    assert data1["id"] == menu_id_1

    # When: 未提供更新欄位
    res = client.patch(f"/api/v1/menu/{menu_id_1}",json={})

    # Then: 回傳錯誤
    assert res.status_code == 400
    data2 = res.json()
    assert "detail" in data2
    assert data2["detail"] == "未提供更新欄位的資料"


# --------------------------------------------------------------
# Delete Menu Test
# --------------------------------------------------------------

def test_delete_one_menu_item_should_succeed():
    clear_db()
    # Given: 新增商品
    menu_id_1 = str(uuid4())
    # When: 加入一筆餐點
    client.post("/api/v1/menu/",
                json={
                    'id': menu_id_1,
                    'name': '牛肉麵',
                    'price': 120,
                    'description': '經典紅燒牛肉麵',
                    'image_url': 'https://example.com/beef.jpg'
                }
    )
    # When: 刪除單筆資料
    response = client.delete(f"/api/v1/menu/{menu_id_1}")
    # Then: 回傳空 byte 物件
    assert response.status_code == 204
    assert response.content == b""

def test_delete_menu_item_not_found_should_fail():
    clear_db()
    # Given: 新增商品
    menu_id_1 = str(uuid4())
    menu_id_2 = str(uuid4())

    # When: 加入第一筆餐點
    client.post("/api/v1/menu/",
                json={
                    'id': menu_id_1,
                    'name': '牛肉麵',
                    'price': 120,
                    'description': '經典紅燒牛肉麵',
                    'image_url': 'https://example.com/beef.jpg'
                }
    )
    # When: 資料不存在
    response = client.delete(f"/api/v1/menu/{menu_id_2}")

    # Then: 回傳錯誤
    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == "Item not found"

