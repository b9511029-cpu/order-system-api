# 李品緯(JasonLee)
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from API作品.app.user import router

# 測試 user api
client = TestClient(router)

# ------------------------------------ 模擬 User database ---------------------------------
users_db : dict ={}

# clean db data
@pytest.fixture(autouse=True)
def db_clear():
    users_db.clear()
    yield
    users_db.clear()

#------------------------- 測試created --------------------------

def test_create_user():
    response = client.post("/api/users/", json={
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@gmail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    })
    assert response.status_code in (200,201)
    data = response.json()
    assert data["user_id"] == 1
    assert data["user_name"] == "Peter"
    assert data["email"] == "xxxxxx@gmail.com"
    assert data["password"] == "123456789"
    assert "created_at" in data
    print('測試成功:建立新增使用者情境')

#--------------------- 測試created duplicate ---------------------
def test_create_user_duplicate():
    payload = {
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@gmail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    }
    client.post("/api/users/", json=payload)
    response2 = client.post("/api/users/", json=payload)
    assert response2.status_code == 409
    data = response2.json()
    assert 'detail' in data
    print('測試成功:使用者已存的情境')
#------------------------ 測試get all users ------------------------
def test_get_all_users():
    client.post("/api/users/", json={
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@gmail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    })
    response = client.get("/api/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == 1
    print('測試成功:建立查詢使用者情境')

#----------------------- 測試get single users -----------------------
def test_get_single_user():
    client.post("/api/users/", json={
        "user_id": 2,
        "user_name": "Tom",
        "email": "yyyyyy@gmail.com",
        "password": "231678998",
        "created_at": datetime.now().isoformat()
    })
    response = client.get("/api/users/2")
    assert response.status_code == 200
    data =  response.json()
    assert data["user_id"] == 2
    assert data["user_name"] == "Tom"
    assert data["email"] == "yyyyyy@gmail.com"
    assert data["password"] == "231678998"
    print('測試成功:建立查詢單一使用者情境')

#------------------ 測試get single users not found ------------------
def test_get_single_user_not_found():
    client.post("/api/users/", json={
        "user_id": 2,
        "user_name": "Tom",
        "email": "yyyyyy@gmail.com",
        "password": "231678998",
        "created_at": datetime.now().isoformat()
    })
    response = client.get("/api/users/3")
    assert response.status_code == 404
    # print(response.status_code)
    data = response.json()
    assert 'detail' in data
    print('測試成功:建立查詢單一使用者失敗情境')

#--------------------- 測試put (update user content) ---------------------
def test_update_user_content():
    original_time = datetime.now() # 建立一個 現在時間的區域變數
    # 新增
    client.post("/api/users/",json={
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": original_time.isoformat()
    })
    # 修改內容
    response = client.put("/api/users/1", json={
        "user_id": 1,
        "user_name": "Amy",
        "email": "yyyyyyy@gmail.com",
        "password": "156489616498",
        "created_at": original_time.isoformat()
    })

    assert response.status_code == 200
    up_data = response.json()
    assert up_data["user_id"] == 1
    assert up_data["user_name"] == "Amy"
    assert up_data["email"] == "yyyyyyy@gmail.com"
    assert up_data["password"] == "156489616498"
    # 國際標準、業界API/Json格式 標準ISO8601,跨系統/語言 都能解析
    assert up_data["created_at"] == original_time.isoformat()
    print("測試成功:建立更新使用者內容情境")

#------------------- 測試 put(item_id not match item.id) -------------------
def test_put_item_id_not_match():
    original_time = datetime.now()
    client.post("/api/users", json={
        "user_id":1,
        "user_name":"Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": original_time.isoformat()
    })
    response = client.put("/api/users/1", json={
        "user_id": 2,
        "user_name": "Amy",
        "email": "yyyyyyy@gmail.com",
        "password": "156489616498",
        "created_at": original_time.isoformat()
    })
    assert response.status_code == 400
    data = response.json()
    assert 'detail' in data
    print('測試成功:建立使用者資料編號錯誤情境')

#------------------------- 測試 put(user not found) -------------------------
def test_put_user_not_found():
    original_time = datetime.now()
    client.post("/api/users", json={
        "user_id": 2,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": original_time.isoformat()
    })
    response = client.put("/api/users/1", json={
        "user_id": 1,
        "user_name": "Amy",
        "email": "yyyyyyy@gmail.com",
        "password": "156489616498",
        "created_at": original_time.isoformat()
    })
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    print('測試成功: 建立修改使用者全部內容')

#---------------------- 測試 patch (update user item) ----------------------
def test_patch_user_item():
    client.post("/api/users/", json={
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    })
    response = client.patch("/api/users/1", json={
        "email": "yyyyyy@mail.com",
    })
    assert response.status_code == 200
    updated = response.json()
    assert updated['email'] == "yyyyyy@mail.com"
    print('測試成功:建立 PATCH 情境')

def test_patch_not_found_user():
    client.post("/api/users/", json={
        "user_id": 999,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    })
    response = client.patch('/api/users/1', json={
        "user_name": 'Amy',
    })
    assert response.status_code == 404
    data = response.json()
    assert 'detail' in data
    print('測試成功: 建立 PATCH 找不到使用者資料情境')


#------------------------ 測試 delete (delete user) ------------------------
def test_delete_user():
    original_time = datetime.now()
    client.post("/api/users/", json={
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": original_time.isoformat()
    })
    response = client.delete("/api/users/1")
    assert response.status_code == 204
    # AssertionError: Status code 204 must not have a response body (204 不能有回應的資料)
    assert response.content == b""
    print('測試成功: 建立刪除使用者情境')








