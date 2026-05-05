# 李品緯(JasonLee)

from uuid import uuid4, UUID
import pytest
from fastapi.testclient import TestClient
from API作品.app.meal_api_main import MenuItem
from API作品.app.cart_api_main import app, cart_db, Cart, CartItem

client = TestClient(app)

# 先建立新增 menu API 邏輯

@pytest.fixture(autouse=True)
def db_clear():
    cart_db.clear()
    yield
    cart_db.clear()

# 業界分層測試:
# 從 API 層測試新增、查詢整體流程
# 從 Cart 層面去測試邏輯 Get、Delete、Patch
#--------------------------------------------------------------
# # API flow 測試整體邏輯沒問題
# Create (已升級完成) 透過API 建立餐點並加入購物車 (完整的整合測試)
#--------------------------------------------------------------
@app.post("/api/v1/menu.db/",status_code=201)
def create_menu(item: MenuItem):
    # 建立餐點邏輯
    return {"id": str(uuid4()),"name": item.name, "price": item.price}

def test_create_menu_item():
    user_id=1
    # print([route.path for route in app.routes]) 可以查詢fastapi讀到那些路由
    # 在發送請求才能找到餐點的路由，這是購物車的測試
    res_menu = client.post("/api/v1/menu.db/",json={
        "name":"Burger",
        "price": 120
    })
    assert res_menu.status_code == 201
    menu_id = res_menu.json()["id"] # 取得UUID

    # 加入購物車
    res_cart = client.post(f"/api/v1/cart/{user_id}/items", json={
        "menu_item_id": str(menu_id), # 將回傳UUID 放入Cart
        "quantity":1
    })
    assert res_cart.status_code == 201
    data = res_cart.json()
    assert data == {"massage":"餐點已加入至購物車"}
    print('\n測試成功:建立餐點加入購物車情境')

    # 檢查資料庫的內部狀態
    cart = cart_db[user_id]
    assert len(cart.items) == 1
    menu_id = UUID(res_menu.json()["id"])
    assert cart.items[0].menu_item_id == menu_id # UUID
    assert cart.items[0].quantity == 1
    print('測試成功:建立檢查購物車資料內容')

    # 再次加入 (測試累加)
    # 當資料庫已存在相同使用者，代表累加產品數量
    res_cart2 = client.post(f"/api/v1/cart/{user_id}/items", json={
        "menu_item_id":str(menu_id), # UUID
        "quantity":2
    })
    assert res_cart2.status_code == 201
    data = res_cart2.json()
    assert data == {"massage":"餐點數量已更新"}
    assert cart.items[0].menu_item_id == menu_id #UUID
    assert cart.items[0].quantity == 3
    print("測試成功:建立使用者更改產品數量情境")

#--------------------------------------------------------------
# API flow 測試整體邏輯沒問題
# Get (使用API建立餐點到加入購物車，完整整合測試)，主要是測試API層
#--------------------------------------------------------------

def test_get_cart():
    user_id = 1

    res_menu = client.post("/api/v1/menu.db/",json={
        "name": "Burger",
        "price": 120
    })
    assert res_menu.status_code == 201
    menu_id= res_menu.json()["id"] # 取得餐點 UUID


    # 餐點 menu_id加入購物車 變成購物車 menu_item_id
    client.post(f"/api/v1/cart/{user_id}/items", json={
        "menu_item_id": menu_id, # UUID 轉成字串
        "quantity": 1
    })
    res = client.get(f"/api/v1/cart/{user_id}/")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == 1
    assert data["items"][0]["menu_item_id"]== menu_id
    assert data["items"][0]["quantity"] == 1
    print("測試成功:查詢使用者購物車情境")

def test_get_cart_items_not_object():
    user_id = 1
    # 測試中，建立一個空購物車
    cart_db[user_id] = Cart(user_id=user_id,items=[],updated_at=datetime.now())
    res_cart = client.get(f"/api/v1/cart/{user_id}/")
    assert res_cart.status_code == 200
    data = res_cart.json()
    assert data["user_id"] == 1
    assert data["items"] == []
    print("測試成功:購物車沒有商品","->",data["items"])

def test_get_cart_not_found():
    user_id = 999 # 假象我資料庫裡目前沒有999 這使用者

    res_cart = client.get(f"/api/v1/cart/{user_id}/")

    assert res_cart.status_code == 404 # 驗證沒有999使用者存在
    data = res_cart.json()
    assert data["detail"] == "Cart not found"
    assert "detail" in data
    print("測試成功：查詢使用者購物車不存在")



#--------------------------------------------------------------
# 快速測邏輯
# 建立測試用購物車，用來測試購物車邏輯 Get 、 delete 、patch
#--------------------------------------------------------------

from datetime import datetime
def setup_cart():
    """建立測試用購物車"""
    cart_db.clear()
    cart_db[1] = Cart(
        user_id=1,
        items=[
            CartItem(menu_item_id=uuid4(),
                     quantity=2,
                     added_at=datetime.now()
                     ),
        ],
        updated_at=datetime.now()
    )
    return cart_db

def setup_empty_cart():
    """建立測試用 空購物車"""
    cart_db.clear()
    cart_db[1] = Cart(
        user_id=1,
        items=[],
        updated_at=datetime.now()
    )
    return cart_db

#--------------------------------------------------------------
# Get
#--------------------------------------------------------------
def test_get_cart_item():
    user_id = 1
    setup_cart()
    menu_item_uuid = cart_db[user_id].items[0].menu_item_id
    menu_item_uuid_str = str(menu_item_uuid)
    response = client.get(f"/api/v1/cart/{user_id}/")
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert data["user_id"] == 1
    assert data["items"][0]["menu_item_id"] == menu_item_uuid_str
    assert data["items"][0]["quantity"] == 2
    print("測試成功:建立查詢購物車")

def test_cart_get_not_found():
    user_id = 999
    setup_cart()
    response = client.get(f"/api/v1/cart/{user_id}/")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Cart not found"
    print('測試成功: 建立購物車不存在情境')

def test_cart_items_zero():
    user_id = 1
    setup_empty_cart()
    response = client.get(f"/api/v1/cart/{user_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert data["items"] == []
    print("測試成功: 建立無商品的購物車情境")
#--------------------------------------------------------------
# Delete
#--------------------------------------------------------------


def test_delete_cart_item():
    user_id = 1
    setup_cart()
    menu_item_uuid = cart_db[user_id].items[0].menu_item_id
    menu_item_uuid_str = str(menu_item_uuid)
    res = client.delete(f"/api/v1/cart/{user_id}/items/{menu_item_uuid_str}/")
    assert res.status_code == 204
    data = res.content
    assert data == b""
    print("測試成功: 建立刪除商品情境")

def test_delete_cart_item_not_found():
    user_id = 1
    setup_cart()
    fake_menu_id = uuid4()
    response = client.delete(f"/api/v1/cart/{user_id}/items/{fake_menu_id}/")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Item not found"
    assert "detail" in data
    print("測試成功: 建立找不到商品情境")

def test_delete_cart_not_found():
    user_id = 1
    setup_cart()
    menu_item_uuid = cart_db[user_id].items[0].menu_item_id
    menu_item_uuid_str = str(menu_item_uuid)
    response = client.delete(f"/api/v1/cart/99/items/{menu_item_uuid_str}/")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Cart not found"
    assert "detail" in data



#--------------------------------------------------------------
# Patch 商品數量
#--------------------------------------------------------------
# 更新商品數量
def test_update_quantity():
    user_id = 1
    setup_cart() # 呼叫 cart.db
    menu_item_id_uuid = cart_db[user_id].items[0].menu_item_id
    menu_item_id_str = str(menu_item_id_uuid)
    res_result = client.patch(f"/api/v1/cart/{user_id}/items/{menu_item_id_str}",
                 json={
                     "quantity": 5
                 })
    assert res_result.status_code == 200
    data = res_result.json()
    assert data["message"] == "item updated"
    print('\n測試成功:更改購物車商品數量')
    # 驗證資料內容
    updated_qty = cart_db[user_id].items[0].quantity
    assert updated_qty == 5
    print(f'測試成功:驗證更新過後的數量:{updated_qty}')

# quantity = 0 → 刪除商品
def test_update_quantity_zero_removes_item():
    user_id = 1
    setup_cart() # provide test data
    # 查詢使用者購物車中的餐點 id,轉換成字串,方便後續 API 串接路徑
    menu_item_id = cart_db[user_id].items[0].menu_item_id
    menu_item_id_str = str(menu_item_id) # API 路徑餐點id.str

    response = client.patch(f"/api/v1/cart/{user_id}/items/{menu_item_id_str}",
                            json={"quantity": 0}
                            )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "item removed"
    assert "message" in data
    # 內部驗證商品已移除
    assert len(cart_db[user_id].items) == 0
    print('測試通過:當購買qty=0,移除該項商品情境')

# 商品不存在 → 404
def test_item_not_found():
    user_id = 1
    setup_cart()
    fake_menu_id = uuid4() # provide fake uuid
    response = client.patch(f"/api/v1/cart/{user_id}/items/{fake_menu_id}",
                            json={"quantity": 4}
                            )
    data = response.json()  # 預期找不到 item
    print("JSON:",data,"->",f"狀態碼:{response.status_code}")
    assert response.status_code == 404
    assert data["detail"] == "Item not found"
    assert "detail" in data
    # 內部驗證 找不到fake_menu_id購物車資料
    assert len(cart_db[user_id].items) == 1 # 驗證僅剩原使用者 1 資料
    assert cart_db[user_id].items[0].menu_item_id != fake_menu_id
    print('測試通過: 建立商品不存在情境')

# 使用者購物車不存在 → 404
def test_cart_not_found():
    user_id = 1
    setup_cart()
    menu_item_uuid = cart_db[user_id].items[0].menu_item_id
    menu_item_uuid_str = str(menu_item_uuid)
    response = client.patch(
                f"/api/v1/cart/999/items/{menu_item_uuid_str}",
                 json={"quantity": 4}
                 )
    data = response.json()
    assert response.status_code == 404
    assert data["detail"] == "Cart not found"
    assert "detail" in data

    # 內部驗證
    assert 999 not in cart_db # 驗證購物車.db(dict)裡沒有 999 key
    assert cart_db[user_id].user_id == 1 # 驗證cart.db 使用者編號欄位沒變
    assert len(cart_db[user_id].items) == 1 # 驗證資料庫長度
    print('測試通過:建立購物車不存在情境')










