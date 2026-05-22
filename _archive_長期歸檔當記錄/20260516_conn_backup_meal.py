# 李品緯(JasonLee)
# 設計 餐點API CRUD
# 設計 資料模型 餐點(編號,名稱,價格,介紹,圖片連結
# 設計 fastapi(post、get、put、delete)
# 測試 (post,get,put,delete)
from pathlib import Path
from typing import List
from uuid import UUID
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
import sqlite3 # SQLite3 資料庫


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

#-------------------------------------------------------------
# 設定檔案路徑 與 sqlite3 資料庫連線
#-------------------------------------------------------------

# 用 pathlib 設定該檔案的完整路徑路徑(現代python 路徑標準庫)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR /"db"/"app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 建立 SQLite connect (開發測試)
conn = sqlite3.connect(DB_PATH,check_same_thread=False)
cursor = conn.cursor() # 查詢 menu.db 檔案
# 建立資料表欄位
cursor.execute("""
CREATE TABLE IF NOT EXISTS menu (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    description TEXT,
    image_url TEXT
)
""")

conn.commit() # 提交連線
conn.close() # 完成請求後，關閉連線
# ----------------------menu_db_Create--------------------------
@app.post("/api/v1/menu/", response_model=MenuItem, status_code=201)
def create_menu_item(item: MenuItem):
    # 建立連線、查詢 menu.db
    conn = sqlite3.connect(DB_PATH,check_same_thread=False)
    cursor = conn.cursor() # 查詢資料庫

    # 發聳post請求
    cursor.execute("SELECT id FROM menu WHERE id = ?",(str(item.id),))
    # SQLite參數只接受tuple/list的資料類型 (tuple,)用逗號判別，代表單個元素，[list],用[]判別
    if cursor.fetchone(): # 讀取一個值， 有值代表資料存在,沒有則為空值
        raise HTTPException(status_code=409,detail="ID already exists")
    cursor.execute("INSERT INTO menu (id,name,price,description,image_url) VALUES (?,?,?,?,?)"
                   ,(
                       str(item.id),
                       item.name,
                       item.price,
                       item.description,
                       item.image_url
                   ))
    conn.commit() # 提交請求
    conn.close() # 關閉連線
    return item # 回傳資料

# ----------------------menu_db_Get all--------------------------
@app.get("/api/v1/menu/",response_model=List[MenuItem])
def get_menu_all():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id,name,price,description,image_url FROM menu")
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
def get_single_menu_item(item_id: UUID):
    conn = sqlite3.connect(DB_PATH)  # 資料接收到請求，找到 menu.db
    cursor = conn.cursor() # 告訴 中介者 我已經在資料庫找到你要的 menu.db

    cursor.execute( # cursor 執行確認資料是否存在
        "SELECT id, name, price, description, image_url FROM menu WHERE id=?",
        (str(item_id),)
    )

    row = cursor.fetchone() # 取得一筆資料 (tuple,)-> [(1, '牛肉麵', 120, '好吃的牛肉麵', '123456')]
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
    return item # id=1 name='牛肉麵' price=120 description='好吃的牛肉麵' image_url='123456'


# ----------------------menu_db_put(整筆內容覆蓋) --------------------------
@app.put("/api/v1/menu/{item_id}", status_code=200)
def update_all_item(item_id: UUID, update_item: MenuItem):
    # id 必須一致
    if item_id != update_item.id:
        raise HTTPException(status_code=400,
                            detail="item_id 與 item.id 不匹配")

    # 連線 SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 確認資料是否存在
    cursor.execute("SELECT id FROM menu WHERE id=?", (str(item_id),))
    row = cursor.fetchone() # 取得並返回 資料
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    # 更新資料
    cursor.execute(
        # 在sql語句中 描述欄位用逗號區隔，欄位與 WHERE id 用逗號區隔，會讓sql 解析成 WHERE id 也是欄位
        # sqlite3.OperationalError: near "WHERE": syntax error (image_url=?, WHERE id=?)
        "UPDATE menu SET name=?, price=?, description=? ,image_url=? WHERE id=?",
        (update_item.name,
                   update_item.price,
                   update_item.description,
                   update_item.image_url,
                   str(item_id)
        ))

    conn.commit()
    conn.close()
    return update_item
    # 執行put 發生回傳 res.status 200, response.json()={},檢查url、 語法、print() ={}
    # find not stop uvicorn server doubt 8000 port 被占用，有沒有結束的資源但是無法清理
    # 重新開機，讓我環境中斷殘留的資源，回傳結果正常

# -------------------------------PATCH 更新 API-------------------------------
@app.patch("/api/v1/menu/{item_id}", response_model=MenuItem)
def update_patch_item(item_id: UUID, item: MenuItemUpdate = ...):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # fetch 可像 dict 指定欄位
    cursor = conn.cursor()

    # 確認該 item 是否存在
    cursor.execute("SELECT * FROM menu WHERE id = ?", (str(item_id),))
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

    sql = f"UPDATE menu SET {set_clause} WHERE id = ?" # 將 sql 子句插入到sql 語法字串中
    cursor.execute(sql, values) # 組成(sql語法，更新參數值)->cursor 與 資料庫 構通更改資料
    conn.commit()

    # 取得更新後的資料
    cursor.execute("SELECT * FROM menu WHERE id = ?", (str(item_id),))
    updated_item = cursor.fetchone()
    conn.close()

    # ** = 字典解包成 關鍵字參數，把 dict 直接傳給 Pydantic 模型或函數,轉成 MenuItem 模型，方便回傳給前端
    return MenuItem(**dict(updated_item))

# -------------------刪除(delete)-------------------------
@app.delete("/api/v1/menu/{item_id}", status_code=204)
def delete_item(item_id: UUID):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 確認該項目是否存在
    cursor.execute("SELECT * FROM menu WHERE id = ?", (str(item_id),))
    stored_item = cursor.fetchone()
    if not stored_item:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Item not found")

    # 刪除項目
    cursor.execute("DELETE FROM menu WHERE id = ?", (str(item_id),))
    conn.commit()
    conn.close()

    return # 204 No Content，不需要回傳 body

