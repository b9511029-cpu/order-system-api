# 李品緯(JasonLee)
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from API作品.db.database import get_db
from API作品.repositories.user_respository import UserRepository

# ----------------------------------- 建立 user API ----------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware, # type: ignore
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#------ uvicorn Re-road time ------
print('載入時間',datetime.now())

#----------------------------------- 註冊 使用者 資料模型 -----------------------------------

class UserItem(BaseModel):
    user_id: int = Field(gt=0)
    user_name: str = Field(min_length=0, max_length=20)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=15)
    created_at: datetime

#------------------------------------- 註冊 使用者 PATCH 專用模型 -------------------------------------
class UserUpdate(BaseModel):
    user_name: str | None = None
    email: str | None = None
    password: str | None = None

#-------------------------------------登入 使用者 模型-------------------------------------
# 使用者登入需求,需與資料庫進行資料比對、驗證
class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=15)


# -----------------------
# POST API: 新增使用者
# -----------------------

@app.post("/api/v1/users", status_code=201, response_model=UserItem)
def created_user(item: UserItem,conn=Depends(get_db)):

    # cursor = conn.cursor()
    user_repo = UserRepository(item,conn) # 組合物件(連線，資料)

    # 檢查 user_id 是否存在
    # cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (item.user_id,))
    rows = user_repo.add_user()

    # if cursor.fetchone():
    if rows:
        raise HTTPException(status_code=409, detail="ID already exists")

    item = user_repo.insert_user_data()
    # 新增資料
    # cursor.execute("""
    #         INSERT INTO users (user_id, user_name, email, password, created_at)
    #         VALUES (?, ?, ?, ?, ?)
    #     """, (
    #     item.user_id,
    #     item.user_name,
    #     item.email,
    #     item.password,
    #     item.created_at.isoformat()
    # ))
    #
    # conn.commit()
    return item

# -----------------------
# GET API: 查詢所有使用者
# -----------------------

@app.get("/api/v1/users", response_model=list[UserItem])
def get_all_users(conn=Depends(get_db)):

    # cursor = conn.cursor()
    #
    # cursor.execute("SELECT user_id, user_name, email, password, created_at FROM users")
    # rows = cursor.fetchall()
    # 完成 sqlite3 拆分
    user_repo = UserRepository(conn)
    rows = user_repo.get_all_users()

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
def get_single_user(user_id: int,conn=Depends(get_db)):

    # cursor = conn.cursor()
    #
    # # 單一查詢
    # cursor.execute(
    #     "SELECT user_id, user_name, email, password, created_at FROM users WHERE user_id = ?",
    #     (user_id,)
    # )
    # row = cursor.fetchone()

    # 找不到使用者回 404

    user_repo = UserRepository(conn)
    row = user_repo.get_user_by_id(user_id)

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
def update_user(user_id: int, user: UserUpdate,conn=Depends(get_db)):

    cursor = conn.cursor()

    # 查詢是否存在該使用者
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()

    if not existing:
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
def delete_user(user_id: int,conn=Depends(get_db)):

    cursor = conn.cursor()

    # 先檢查使用者是否存在
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="user not found")

    # 刪除使用者
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()

    return  # 204 表示成功但沒有回傳內容

# -----------------------------
# Use login API: 使用者登入
# -----------------------------
@app.post("/api/v1/login", status_code=200)
def login(user: UserLogin,conn=Depends(get_db)):

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))

    user_item = cursor.fetchone()

    if not user_item:
        raise HTTPException(status_code=404, detail="使用者不存在")

    if user_item["password"] != user.password:
        raise HTTPException(status_code=401, detail="密碼錯誤")

    return {"message": "登入成功"}
