# 李品緯(JasonLee)
from typing import List
from uuid import UUID
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from API作品.db.database import get_db
from API作品.repositories.meal_repository import MealRepository

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"], # 允許所有來源
    allow_methods=["*"],      # 允許所有 HTTP 方法
    allow_headers=["*"],      # 允許所有 headers
)

# 建立餐點模型
class MenuItem(BaseModel):
    id: UUID | None = None
    name: str = Field(min_length=1,max_length=15)
    price: int = Field(gt=0)
    description: str | None = None # python 3.10+ 資料可寫可不寫，預設:None
    image_url: str | None = None

# 建立patch專用資料模型，欄位可填可不填
class MenuItemUpdate(BaseModel):
    name: str | None = None
    price: int | None = None
    description: str | None = None
    image_url: str | None = None


@app.post("/api/v1/menu", response_model=MenuItem, status_code=201)
def create_menu_item(item: MenuItem,conn=Depends(get_db)):

    # cursor = conn.cursor()
    # cursor.execute("SELECT id FROM menus WHERE id = ?",(str(item.id),))
    meal_repo = MealRepository(conn)

    meal_id = meal_repo.get_meal_id_by_id(item.id)

    if meal_id:
        raise HTTPException(status_code=409,detail="ID already exists")

    # cursor.execute("INSERT INTO menus (id,name,price,description,image_url) VALUES (?,?,?,?,?)"
    #                ,(
    #                    str(item.id),
    #                    item.name,
    #                    item.price,
    #                    item.description,
    #                    item.image_url
    #                ))
    # conn.commit()
    meal_repo.create_meal_data(item.id,
                               item.name,
                               item.price,
                               item.description,
                               item.image_url)
    return item

# ----------------------menu_db_Get all--------------------------
@app.get("/api/v1/menu",response_model=List[MenuItem])
def get_menu_all(conn=Depends(get_db)):
    # cursor = conn.cursor()
    # cursor.execute("SELECT id,name,price,description,image_url FROM menus")
    # rows = cursor.fetchall()
    meal_repo = MealRepository(conn)

    meal_rows = meal_repo.get_all_meals()

    menu_items = [
        MenuItem(
            id = row["id"],
            name = row["name"],
            price = row["price"],
            description = row["description"],
            image_url = row["image_url"]
        )for row in meal_rows
    ]
    return menu_items

# ----------------------menu_db_single_Get --------------------------
@app.get("/api/v1/menu/{item_id}", response_model=MenuItem, status_code=200)
def get_single_menu_item(item_id: UUID,conn=Depends(get_db)):

    # cursor = conn.cursor()
    # cursor.execute(
    #     "SELECT id, name, price, description, image_url FROM menus WHERE id=?",
    #     (str(item_id),)
    # )
    # row = cursor.fetchone()
    meal_repo = MealRepository(conn)
    meal_rows = meal_repo.get_meal_by_id(item_id)

    if meal_rows is None:
        raise HTTPException(status_code=404,detail=f"item not found, 編號:{item_id} 不存在")

    item = MenuItem(
        id = meal_rows["id"],
        name = meal_rows["name"],
        price = meal_rows["price"],
        description = meal_rows["description"],
        image_url = meal_rows["image_url"]
    )
    return item


# ----------------------menu_db_put(整筆內容覆蓋) --------------------------
@app.put("/api/v1/menu/{item_id}", status_code=200)
def update_all_item(item_id: UUID, update_item: MenuItem,conn=Depends(get_db)):
    # id 必須一致
    if item_id != update_item.id:
        raise HTTPException(status_code=400,
                            detail="item_id 與 item.id 不匹配")

    cursor = conn.cursor()

    # 確認資料是否存在
    cursor.execute("SELECT id FROM menus WHERE id=?", (str(item_id),))
    row = cursor.fetchone() # 取得並返回 資料
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # 更新資料
    cursor.execute(
        "UPDATE menus SET name=?, price=?, description=? ,image_url=? WHERE id=?",
        (update_item.name,
         update_item.price,
         update_item.description,
         update_item.image_url,
         str(item_id)
        ))

    conn.commit()
    return update_item

# -------------------------------PATCH 更新 API-------------------------------
@app.patch("/api/v1/menu/{item_id}", response_model=MenuItem)
def update_patch_item(item_id: UUID, item: MenuItemUpdate = ...,conn=Depends(get_db)):

    cursor = conn.cursor()

    # 確認該 item 是否存在
    cursor.execute("SELECT * FROM menus WHERE id = ?", (str(item_id),))
    stored_item = cursor.fetchone()
    if not stored_item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    # 準備局部更新欄位
    # item.dict(exclude_unset=True):V2.過時版本,現在業界實務做法 model_dump(),完全向後兼容 Pydantic v2 的新 API
    # 只抓使用者在 PATCH 中實際傳入的欄位,沒有傳的欄位不會包含在 dict 裡
    update_data = item.model_dump(exclude_unset=True)
    if not update_data:
        conn.close()
        raise HTTPException(status_code=400, detail="未提供更新欄位的資料")

    # 動態生成 SQL 更新語句，防止惡意修改
    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values()) # values ['牛肉麵', 120, '好吃的']
    values.append(str(item_id))  # WHERE id = ?

    sql = f"UPDATE menus SET {set_clause} WHERE id = ?" # 將 sql 子句插入到sql 語法字串中
    cursor.execute(sql, values) # 組成(sql語法，更新參數值)->cursor 與 資料庫 構通更改資料
    conn.commit()

    # 取得更新後的資料
    cursor.execute("SELECT * FROM menus WHERE id = ?", (str(item_id),))
    updated_item = cursor.fetchone()
    conn.close()

    # ** = 字典解包成 關鍵字參數，把 dict 直接傳給 Pydantic 模型或函數,轉成 MenuItem 模型，方便回傳給前端
    return MenuItem(**dict(updated_item))

# -------------------刪除(delete)-------------------------
@app.delete("/api/v1/menu/{item_id}", status_code=204)
def delete_item(item_id: UUID,conn=Depends(get_db)):

    cursor = conn.cursor()

    # 確認該項目是否存在
    cursor.execute("SELECT * FROM menus WHERE id = ?", (str(item_id),))
    stored_item = cursor.fetchone()
    if not stored_item:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Item not found")

    # 刪除項目
    cursor.execute("DELETE FROM menus WHERE id = ?", (str(item_id),))
    conn.commit()
    conn.close()

    return # 204

