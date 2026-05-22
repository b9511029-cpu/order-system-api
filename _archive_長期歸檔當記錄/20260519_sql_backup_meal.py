# 李品緯(JasonLee)
from typing import List
from uuid import UUID
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from API作品.db.database import get_db

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


@app.post("/api/v1/menu/", response_model=MenuItem, status_code=201)
def create_menu_item(item: MenuItem,conn=Depends(get_db)):

    cursor = conn.cursor()

    # 發聳post請求
    cursor.execute("SELECT id FROM menus WHERE id = ?",(str(item.id),))
    # SQLite參數只接受tuple/list的資料類型 (tuple,)用逗號判別，代表單個元素，[list],用[]判別
    if cursor.fetchone(): # 讀取一個值， 有值代表資料存在,沒有則為空值
        raise HTTPException(status_code=409,detail="ID already exists")
    cursor.execute("INSERT INTO menus (id,name,price,description,image_url) VALUES (?,?,?,?,?)"
                   ,(
                       str(item.id),
                       item.name,
                       item.price,
                       item.description,
                       item.image_url
                   ))
    conn.commit()
    conn.close()
    return item

# ----------------------menu_db_Get all--------------------------
@app.get("/api/v1/menu/",response_model=List[MenuItem])
def get_menu_all(conn=Depends(get_db)):

    cursor = conn.cursor()

    cursor.execute("SELECT id,name,price,description,image_url FROM menus")
    rows = cursor.fetchall()

    cursor.close()
    menu_items = [
        MenuItem(
            id = row[0],
            name = row[1],
            price = row[2],
            description = row[3],
            image_url = row[4]
        )for row in rows
    ]
    return menu_items

# ----------------------menu_db_single_Get --------------------------
@app.get("/api/v1/menu/{item_id}", response_model=MenuItem, status_code=200)
def get_single_menu_item(item_id: UUID,conn=Depends(get_db)):

    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, price, description, image_url FROM menus WHERE id=?",
        (str(item_id),)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404,detail=f"item not found, 編號:{item_id} 不存在")

    item = MenuItem(               # response_model=MenuItem => response schema filtering
        id = row[0],               # schema(模式),控制核心:控制回傳資料的結構與欄位
        name = row[1],             # 當你回傳的是資料模型時，API 只會回傳資料結構與欄位，其他會過濾掉
        price = row[2],            # 達到控制 API 輸出的模式，讓前端拿到你定義的欄位,隱藏敏感資料
        description = row[3],
        image_url = row[4]
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
        conn.close()
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
    conn.close()
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

