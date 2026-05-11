# 李品緯(JasonLee)
import sqlite3
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from API作品.app.user import app, DB_PATH

# 測試 user api
client = TestClient(app)

# -----------------------------
# auto db clear
# -----------------------------
@pytest.fixture(autouse=True)
def clear_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        yield

#-------------------------
# creat
# --------------------------

def test_create_user_should_succeed():
    # Arrange (準備資料)
    payload = {
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@gmail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    }
    # Act (呼叫 API)
    response = client.post("/api/v1/users", json=payload)
    # Assert (驗證成功)
    assert response.status_code in (200,201)
    data = response.json()
    assert data["user_id"] == 1
    assert data["user_name"] == "Peter"
    assert data["email"] == "xxxxxx@gmail.com"
    assert data["password"] == "123456789"
    assert "created_at" in data

#--------------------- 測試created duplicate ---------------------
def test_create_user_duplicate_should_fail():
    # Arrange (準備資料)
    payload = {
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@gmail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    }
    # Act (呼叫 API)
    client.post("/api/v1/users", json=payload)
    response2 = client.post("/api/v1/users", json=payload)
    # Assert (驗證錯誤)
    assert response2.status_code == 409
    data = response2.json()
    assert 'detail' in data

#------------------------ 測試get all users ------------------------
def test_get_all_users_should_succeed():
    # Arrange (準備資料)
    payload = {
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@gmail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    }

    # Act (呼叫 API)
    client.post("/api/v1/users", json=payload)
    response = client.get("/api/v1/users")

    # Assert (驗證成功)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == 1

#----------------------- 測試 get single users -----------------------
def test_get_single_user_should_succeed():
    # Arrange (準備資料)
    payload = {
        "user_id": 2,
        "user_name": "Tom",
        "email": "yyyyyy@gmail.com",
        "password": "231678998",
        "created_at": datetime.now().isoformat()
    }

    # Act (呼叫 API)
    client.post("/api/v1/users/", json=payload)
    response = client.get("/api/v1/users/2")

    # Assert (驗證成功)
    assert response.status_code == 200
    data =  response.json()
    assert data["user_id"] == 2
    assert data["user_name"] == "Tom"
    assert data["email"] == "yyyyyy@gmail.com"
    assert data["password"] == "231678998"

#------------------ 測試get single users not found ------------------
def test_get_single_user_not_found_should_fail():
    # Arrange (準備資料)
    payload = {
        "user_id": 2,
        "user_name": "Tom",
        "email": "yyyyyy@gmail.com",
        "password": "231678998",
        "created_at": datetime.now().isoformat()
    }

    # Act (呼叫 API)
    client.post("/api/v1/users/", json=payload)
    response = client.get("/api/v1/users/3")

    # Assert (驗證錯誤)
    assert response.status_code == 404
    # print(response.status_code)
    data = response.json()
    assert 'detail' in data


#---------------------- 測試 patch (update user item) ----------------------
def test_patch_user_item_should_succeed():
    # Arrange (準備資料)
    payload = {
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    }

    update = {"email": "yyyyyy@mail.com"}

    # Act (呼叫 API)
    client.post("/api/v1/users", json=payload)
    response = client.patch("/api/v1/users/1", json=update)

    # Assert (驗證成功)
    assert response.status_code == 200
    updated = response.json()
    assert updated['email'] == "yyyyyy@mail.com"

def test_patch_user_not_found_should_fail():
    # Arrange (準備資料)
    payload = {
        "user_id": 999,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    }

    update = {"user_name": 'Amy'}

    # Act (呼叫 API)
    client.post("/api/v1/users", json=payload)
    response = client.patch("/api/v1/users/1", json=update)

    # Assert (驗證失敗)
    assert response.status_code == 404
    data = response.json()
    assert 'detail' in data


#------------------------ 測試 delete (delete user) ------------------------
def test_delete_user_should_succeed():
    # Arrange (準備資料)
    payload = {
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    }

    # Act (呼叫 API)
    client.post("/api/v1/users/", json=payload)
    response = client.delete("/api/v1/users/1")

    # Assert (驗證成功)
    assert response.status_code == 204
    # AssertionError: Status code 204 must not have a response body (204 不能有回應的資料)
    assert response.content == b""

def test_delete_user_not_found_should_fail():
    # Arrange (準備資料)
    payload = {
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxx@mail.com",
        "password": "123456789",
        "created_at": datetime.now().isoformat()
    }

    # Act (呼叫 API)
    client.post("/api/v1/users/", json=payload)
    response = client.delete("/api/v1/users/2")

    # Assert (驗證失敗)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "user not found"


#------------------------ 測試 login (user login)  ------------------------

def test_user_login_should_succeed():
    # Given: Arrange (準備資料)
    original_time = datetime.now()
    create_res = client.post("/api/v1/users/", json={
        "user_id": 1,
        "user_name": "Peter",
        "email": "12345678@mail.com",
        "password": "0912345678",
        "created_at": original_time.isoformat()
    })
    assert create_res.status_code == 201
    db_user = create_res.json()

    payload = {
        "email": "12345678@mail.com",
        "password": "0912345678"
    }

    # When: Act (呼叫API)
    login_res = client.post("/api/v1/login", json=payload)

    # Then: Assert (驗證成功)
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["message"] == "登入成功"

def test_user_login_not_found_should_fail():
    # Given: Arrange (準備資料)
    original_time = datetime.now()
    client.post("/api/v1/users/", json={
        "user_id": 1,
        "user_name": "Peter",
        "email": "xxxxxxxxx@mail.com",
        "password": "0912345678",
        "created_at": original_time.isoformat()
    })

    payload = {
        "email": "12345678@mail.com",
        "password": "0912345678"
    }

    # When: Act (呼叫API)
    login_res = client.post("/api/v1/login", json=payload)

    # Then: Assert (驗證成功)
    assert login_res.status_code == 404
    data = login_res.json()
    assert data["detail"] == "使用者不存在"


def test_user_login_password_err_should_fail():
    # Given: Arrange (準備資料)
    original_time = datetime.now()
    client.post("/api/v1/users/", json={
        "user_id": 1,
        "user_name": "Peter",
        "email": "12345678@mail.com",
        "password": "0912345678",
        "created_at": original_time.isoformat()
    })

    payload = {
        "email": "12345678@mail.com",
        "password": "123456789"
    }

    # When: Act (呼叫API)
    login_res = client.post("/api/v1/login", json=payload)

    # Then: Assert (驗證成功)
    assert login_res.status_code == 401
    data = login_res.json()
    assert data["detail"] == "密碼錯誤"

