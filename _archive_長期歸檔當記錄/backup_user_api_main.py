# 李品緯(JasonLee)
# 使用者 API CRUD
# 設計 資料模型 使用者(user_id,username,email,password,created_at)
# 設計 (post、get、update、patch、delete)
# 測試 (post、get、update、patch、delete)
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

# ----------------------------------- 建立 user API ----------------------------------------
app = FastAPI(title="UsersItem API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#------ uvicorn Re-road time ------
print('載入時間',datetime.now())

# ---------------------------------- 建立 使用者 資料模型 -----------------------------------
class UserItem(BaseModel):
    user_id: int = Field(gt=0)
    user_name: str = Field(min_length=0, max_length=20)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=15)
    created_at: datetime

#------------------------------------- PATCH 專用模型 -------------------------------------
class UserUpdate(BaseModel):
    user_name: str | None = None
    email: str | None = None
    password: str | None = None

#-------------------------------------登入 使用者 模型-------------------------------------
# 使用者登入需求,需與資料庫進行資料比對、驗證
class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=15)

# ------------------------------------ 模擬 User database ---------------------------------
users_db : dict[int, UserItem] ={}


#----------------- 建立 SQLite 3 connect (Development and testing 開發測試) -----------------
import sqlite3 # sqlite 資料庫 全域變數
conn = sqlite3.connect("users.db", check_same_thread=False) # Establish(建立) a database

cursor = conn.cursor() # cursor(游標)物件 ， 像 一個全能型助理，幫你操作與管理資料庫的助理，並返回結果，會自動轉成python的語言
# 建立 user.db 資料庫表單，在表單中建立使用者資料欄位
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
               user_id INTEGER PRIMARY KEY,
               user_name TEXT NOT NULL,
               email TEXT NOT NULL,
               password TEXT NOT NULL,
               created_at TEXT NOT NULL
)
""")
conn.commit() # 提交連線
conn.close() # 關閉連線
#------------------------------------- 資料庫建檔完成 -------------------------------------

# -----------------------
# POST API: 新增使用者
# -----------------------
@app.post("/api/v1/users/", status_code=201, response_model=UserItem)
def created_user(item: UserItem):
    # 直接連 SQLite
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    # 檢查 user_id 是否存在
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (item.user_id,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="ID already exists")

    # 新增資料
    cursor.execute("""
            INSERT INTO users (user_id, user_name, email, password, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
        item.user_id,
        item.user_name,
        item.email,
        item.password,
        item.created_at.isoformat()
    ))

    conn.commit()
    conn.close()  # <- 在最後才關閉連線

    return item

# -----------------------
# GET API: 查詢所有使用者 (使用者通常設計給系統管理查看，前端網頁不會設計這個功能)
# -----------------------

@app.get("/api/v1/users/", response_model=list[UserItem])
def get_all_users():
    # 直接開啟連線
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    # 沒設定 row_factory(預設只能用列表索引存取資料)，但是有設定可以透過工廠方法，改成sqlite3.row 物件(可用字典key取欄位的職)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, user_name, email, password, created_at FROM users")
    rows = cursor.fetchall()
    conn.close()

    # 轉換 created_at 並回傳
    users_items = [
        UserItem(
            user_id=row["user_id"],
            user_name=row["user_name"],
            email=row['email'],
            password=row['password'],
            created_at=datetime.fromisoformat(row["created_at"])
        )
        for row in rows
    ]
    return users_items

# -----------------------
# GET ONE API: 查詢單一使用者
# -----------------------
@app.get("/api/v1/users/{user_id}", response_model=UserItem)
def get_single_user(user_id: int):
    # 連線 SQLite
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row  # 這樣 row 可以用 key 取欄位
    cursor = conn.cursor()

    # 單一查詢
    cursor.execute(
        "SELECT user_id, user_name, email, password, created_at FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    # 找不到使用者回 404
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 轉換 datetime 並回傳
    user_item = UserItem(
        user_id=row["user_id"],
        user_name=row["user_name"],
        email=row["email"],
        password=row["password"],
        created_at=datetime.fromisoformat(row["created_at"])
    )
    return user_item

# -----------------------
# PATCH API: 更新使用者(局部)
# -----------------------
@app.patch("/api/v1/users/{user_id}", response_model=UserItem)
def update_user(user_id: int, user: UserUpdate):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 查詢是否存在該使用者
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # 根據傳入資料更新欄位，沒有提供的就保留原值
    new_name = user.user_name if user.user_name is not None else existing["user_name"]
    new_email = user.email if user.email is not None else existing["email"]
    new_password = user.password if user.password is not None else existing["password"]

    # 更新資料庫
    cursor.execute(
        "UPDATE users SET user_name = ?, email = ?, password = ? WHERE user_id = ?",
        (new_name, new_email, new_password, user_id)
    )
    conn.commit()

    # 取得更新後的資料
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    updated = cursor.fetchone()
    conn.close()

    user_item = UserItem(
        user_id=updated["user_id"],
        user_name=updated["user_name"],
        email=updated["email"],
        password=updated["password"],
        created_at=datetime.fromisoformat(updated["created_at"])
    )
    return user_item

# -----------------------
# DELETE API: 刪除使用者
# -----------------------
@app.delete("/api/v1/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    # 先檢查使用者是否存在
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # 刪除使用者
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    # 204 表示成功但沒有回傳內容
    return

# -----------------------------
# Use login API: 使用者登入
# 使用者登入不會回傳使用者內容，通常只會回傳登入是否成功
# -----------------------------
@app.post("/api/v1/login/", status_code=200)
def login(user: UserLogin):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    db_user = cursor.fetchone()
    conn.close()

    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    if db_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="密碼錯誤")

    return {"message": "登入成功"}










#-----------------------------------------------------------------------------------------
#                                    old Use API
#-----------------------------------------------------------------------------------------

# ------------------------------------- Create -------------------------------------------
@app.post("/api/users/", status_code=201, response_model=UserItem)
def created_user(item: UserItem):
    if item.user_id in users_db:
        raise HTTPException(status_code=409, detail='ID already exists')

    users_db[item.user_id] = item

    return item

# ---------------------------------------- Read -------------------------------------------
@app.get("/api/users/", status_code=200, response_model=list[UserItem])
def get_all_users():

    return list(users_db.values())

# --------------------------------------- Read one ----------------------------------------
@app.get("/api/users/{user_id}", status_code=200, response_model=UserItem)
def get_single_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="user not found")

    return users_db[user_id]

#------------------------------------------- Put -------------------------------------------
# PUT：理論存在，但實務很少用，容易發生 整筆_覆蓋，風險太高
@app.put("/api/users/{user_id}", status_code=200, response_model=UserItem)
def update_user_content(user_id: int, item: UserItem):
    if user_id != item.user_id:
        raise HTTPException(status_code=400, detail="item_id not match item.id")
    if item.user_id not in users_db:
        raise HTTPException(status_code=404, detail="user not found or does not exist user_db")

    users_db[user_id] = item
    return item
#------------------------------------------ PATCH ------------------------------------------
@app.patch("/api/users/{user_id}", status_code=200, response_model=UserUpdate)
def patch_user_content(user_id: int, item: UserUpdate):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail='user not found or does not exist user_db')
    # 原始資料
    existing_data = users_db[user_id] # value : UserItem (物件)
    # 接收更新的欄位
    update_data =  item.model_dump(exclude_unset=True)

    # 更新使用者資料
    updated_user = existing_data.model_dump() # 將從資料庫取出的(物件)資料轉換成字典 (使用者資料 = UserItem (物件))
    updated_user.update(update_data) # 將資料庫裡的物件與更新欄位的物件 都轉換成字典類型，就可以進行 update()

    # 更新後的字典資料轉換成 UserItem
    users_db[user_id] = UserItem(**updated_user) # ** 解包 dict ,* 解包 list/tuple

    return UserItem
#------------------------------------- delete one user -------------------------------------
@app.delete("/api/users/{user_id}",status_code=204)
def delete_one_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail=f"user not found or {user_id}號 user does not exist user_db")

    del users_db[user_id]

    return



