# 李品緯(JasonLee)
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from API作品.db.database import get_db
from API作品.repositories.user_repository import UserRepository

# ----------------------------------- 建立 user API ----------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware, # type: ignore
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#------ uvicorn Re-road time ------
print('載入時間',datetime.now().isoformat())

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
def created_user(items:UserItem,conn=Depends(get_db)):

    user_repo = UserRepository(conn)

    rows = user_repo.get_user_by_id(user_id=items.user_id)

    if rows:
        raise HTTPException(status_code=409, detail="ID already exists")

    item = user_repo.create_user_data(items)

    return item

# -----------------------
# GET API: 查詢所有使用者
# -----------------------

@app.get("/api/v1/users", response_model=list[UserItem])
def get_all_users(conn=Depends(get_db)):

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

    user_repo = UserRepository(conn)

    row = user_repo.get_user_by_id(user_id=user_id)

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

    user_repo = UserRepository(conn)

    existing = user_repo.get_user_by_id(user_id)

    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    # 更新:根據傳入資料更新欄位，沒有提供的就保留原值
    new_name = user.user_name if user.user_name is not None else existing["user_name"]
    new_email = user.email if user.email is not None else existing["email"]
    new_password = user.password if user.password is not None else existing["password"]

    user_repo.update_user_by_id(new_name=new_name,
                                new_email=new_email,
                                new_password=new_password,
                                user_id=user_id)
    # 查詢: 使用者更新後資料
    updated = user_repo.get_user_by_id(user_id=user_id)

    # 用 module Schema(模式) 控制輸出結構
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

    user_repo = UserRepository(conn)

    # 查巡使用者是否存在
    rows = user_repo.get_user_by_id(user_id=user_id)

    if not rows:
        raise HTTPException(status_code=404, detail="user not found")

    # 刪除使用者
    user_repo.delete_user_by_id(user_id=user_id)

    return  # 204 表示成功但沒有回傳內容

# -----------------------------
# Use login API: 使用者登入
# -----------------------------
@app.post("/api/v1/login", status_code=200)
def login(user: UserLogin,conn=Depends(get_db)):

    user_repo = UserRepository(conn)

    user_login = user_repo.get_user_by_email(email=user.email)

    if not user_login:
        raise HTTPException(status_code=404, detail="使用者不存在")

    if user_login["password"] != user.password:
        raise HTTPException(status_code=401, detail="密碼錯誤")

    return {"message": "登入成功"}
