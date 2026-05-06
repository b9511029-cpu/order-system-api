# 李品緯(JasonLee)
# 購物車 API CRUD，包含 post(新增商品)、get(查詢清單所有商品)、delete(刪除商品)、patch(修改商品內容)
# 設計 資料模型 購物車清單()
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import sqlite3

app = FastAPI()

#-----------------
# 模擬 db
#-----------------
cart_db = {} # user_id -> Cart

now = datetime.now()
print("Reload",now)

#--------------------------------------------------------------------------
# 購物車 Internal data Model (負責維護系統邏輯、統計商品、數量、計算最後購買總金額
#--------------------------------------------------------------------------

class CartItem(BaseModel):
    id: UUID
    menu_item_id: UUID
    quantity: int = Field(gt=0, le=20)
    added_at: datetime

# 購物車主體，也就是顯示所有商品清單
class Cart(BaseModel):
    id: UUID
    user_id: int = Field(gt=0)
    items: List[CartItem] = Field(default_factory=list)
    updated_at: datetime

#--------------------------------------------------------------
# Apply Front User Request Models (負責新增、驗證資料)
#--------------------------------------------------------------
class AddCartItemRequest(BaseModel):
    menu_item_id: UUID
    quantity: int = Field(gt=0,le=20)
#--------------------------------------------------------------
# update(patch) Models (負責更改產品數量)
#--------------------------------------------------------------
class UpdateCartItemRequest(BaseModel):
    quantity: int | None = Field(default=None, ge=0)

#--------------------------------------------------------------
# Response Front User update Cart data Models (負責回應前端結果)
#--------------------------------------------------------------
class CartItemResponse(BaseModel): # 回應使用者,購物車商品資料
    menu_item_id: UUID
    quantity: int

class CartResponse(BaseModel):     # 回應購物車清單給使用者
    user_id: int
    cart_id: UUID
    updated_at: str
    items: List[CartItemResponse]

class MessageResponse(BaseModel):  # 回傳通知訊息，delete response 204 not content
    massage: str


#---------------------
# Set connect path
#---------------------
# 使用 pathlib 設定 db_path 絕對路徑
BASE_DIR = Path(__file__).resolve().parent.parent # 找到這個檔案的根目錄
DB_PATH = BASE_DIR /"db"/"test.db" # 將根目錄的路徑+資料庫的路徑 = 資料庫完整路徑(提供給資料庫連線使用)
DB_PATH.parent.mkdir(parents=True, exist_ok=True) # 確保資料夾存在，如果不存在就幫你建立(自動補齊環境差異)

#--------------------------------------
# 建立 sqlite3.connect and test conn
#--------------------------------------
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys=ON") # 將外鍵功能打開，OFF 只會刪除Cart 不會刪除item
cursor = conn.cursor()

#-------------------------------------------
# 將 API 改成 支援 DI(dependency Injection)
# 目前API 使用的正式環境
#-------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn # yield 代表產量 ,產量前(提供DB)/產量後(自動清理)
    finally:
        conn.close()


#------------------------
# 建立 Carts TABLE
#------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS carts (
    id TEXT PRIMARY KEY,
    user_id INTEGER UNIQUE,
    updated_at TEXT NOT NULL 
)
""")
#------------------------
# 建立 CartItem TABLE
#------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS cart_items (
    id TEXT PRIMARY KEY,
    cart_id TEXT NOT NULL,
    menu_item_id TEXT NOT NULL,
    quantity INTEGER,
    added_at TEXT NOT NULL,
    UNIQUE (cart_id, menu_item_id),
    FOREIGN KEY (cart_id) REFERENCES carts (id) ON DELETE CASCADE
)
""")
# CHECK(quantity > 0 AND quantity < 20) 防止任何繞過 API 的寫入造成資料污染
conn.commit()
conn.close()

#----------------------------
# SQLite + Add Cart
#----------------------------
@app.post("/api/v2/cart/{user_id}/items",status_code=201,response_model=CartResponse)
def add_to_cart(user_id: int, data: AddCartItemRequest):
    # 建立時間
    now_taipei = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Taipei")).isoformat()

    # 建立連線
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON") # 打開外鍵功能
    cursor = conn.cursor() # 呼叫 cursor

    # 查詢 cart 資料表 是否存在 使用者購物車編號
    cursor.execute("SELECT id FROM carts WHERE user_id = ?",(user_id,))

    # 先確認 carts TABLE 是否存在使用者.cart_id
    row = cursor.fetchone()

    # cart not exist-> create cart
    if row is None:
        cart_id = str(uuid4())  # 建立 cart_id
        cursor.execute("INSERT INTO carts(id, user_id, updated_at) VALUES(?,?,?)",
                       (cart_id,user_id,now_taipei)
                       )
    # cart exist -> Keep use
    else:
        cart_id = row[0]


    # 更改購物車商品數量，查詢購物車資料表欄位
    cursor.execute("""SELECT quantity FROM cart_items 
                          WHERE cart_id = ? AND menu_item_id = ? """,
                    (cart_id, str(data.menu_item_id))
    )
    # pick DB quantity value
    existing_quantity = cursor.fetchone() # 已存在tuple

    # 確認 quantity 不是空值
    if existing_quantity is not None:
        current_quantity = existing_quantity[0] # 取得tuple 中的數值

        # ***加入累加後超過上限檢查 [Guard Clause（防衛式寫法）]
        if current_quantity + data.quantity > 20: # 累加結果 > 20 會執行raise 中斷
            raise HTTPException(status_code=400,detail="Total quantity cannot exceed 20")

        # 當累加結果<20，沒有執行raise 會自然執行 更改數量
        cursor.execute("""UPDATE cart_items SET quantity = quantity + ?
                              WHERE cart_id = ? AND menu_item_id = ? """,
                       (data.quantity, cart_id, str(data.menu_item_id))
                        )
    # 無數量欄位，代表要加入新的商品
    else:
        cursor.execute("""
                            INSERT INTO cart_items (id, cart_id, menu_item_id, quantity, added_at)
                            VALUES (? ,? ,? ,?,? ) """,
                       (
                            str(uuid4()),
                            cart_id,
                            str(data.menu_item_id),
                            data.quantity,
                            now_taipei
                       )
        )

    # 建立購物車最後更新時間
    cursor.execute("UPDATE carts SET updated_at = ? WHERE id = ? ",
                   (now_taipei, cart_id))

    # 查出最新 items
    cursor.execute("""SELECT menu_item_id,quantity FROM cart_items 
                          WHERE cart_id = ? """,
                   (cart_id,)
    )

    items = cursor.fetchall()

    # 最後提交
    conn.commit()
    conn.close()

    final_cart = (
        CartResponse(
            user_id = user_id,
            cart_id = cart_id,
            updated_at= now_taipei,
            items =[CartItemResponse(menu_item_id=i[0],quantity=i[1])
                                    for i in items]
            )
    )
    return final_cart

#----------------------------
# SQLite + Get Cart + 測試框架
#----------------------------
@app.get("/api/v2/cart/{user_id}",response_model=CartResponse)
def get_cart(user_id: int,conn=Depends(get_db)):

    cursor = conn.cursor()

    cursor.execute("SELECT id, updated_at FROM carts WHERE user_id = ?"
                   ,(user_id,))

    c_row = cursor.fetchone()

    if c_row is None:
        raise HTTPException(status_code=404, detail="cart not found")

    # Supply cart_id
    cart_id , updated_at = c_row # tuple unpacking (解構/結構對應)

    cursor.execute("SELECT menu_item_id, quantity FROM cart_items WHERE cart_id = ?"
                   ,(cart_id,))

    ci_rows = cursor.fetchall()

    cart_response = CartResponse(
        user_id = user_id,
        cart_id = cart_id,
        updated_at = updated_at,
        items = [
            CartItemResponse(
                menu_item_id = menu_item_id,
                quantity = quantity
            )
            for menu_item_id,quantity in ci_rows # 這裡改成 unpacking(結構對應/解構)
        ]

    )
    return cart_response


#-------------------------------------------------------
# SQLite + Patch Cart
# (購物車通常都是局部修改居多，真實場景很少使用的put(因此沒有設計))
#-------------------------------------------------------
@app.patch("/api/v2/cart/{user_id}/items/{menu_item_id}",response_model=CartResponse)
def patch_cart_items(user_id: int, menu_item_id: UUID, data: UpdateCartItemRequest,conn=Depends(get_db)):
    # 先查詢購物車
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM carts WHERE user_id = ?",(user_id,))

    c_row = cursor.fetchone() # tuple (cart_id,)

    # 判斷是否購物車是否存在
    if c_row is None:
        raise HTTPException(status_code=404, detail="cart not found")

    cart_id = c_row[0]  # tuple unpacking

    cursor.execute("SELECT quantity FROM cart_items WHERE cart_id = ? AND menu_item_id = ?",
                   (cart_id,str(menu_item_id))
    )

    ci_item = cursor.fetchone()

    if ci_item is None:
        raise HTTPException(status_code=404, detail="cart items not found")

    #　更新
    new_qty = data.quantity

    if new_qty > 20:
        raise HTTPException(status_code=400, detail="quantity cannot be greater than 20")

    if new_qty == 0:
        cursor.execute("DELETE FROM cart_items WHERE cart_id = ? AND menu_item_id = ?",
                       (cart_id,str(menu_item_id))
        )

    else:
        cursor.execute("UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND menu_item_id = ?",
                       (new_qty,cart_id,str(menu_item_id))
        )

    # 查詢最新 cart
    cursor.execute(""" SELECT menu_item_id, quantity FROM cart_items 
                       WHERE cart_id = ? """,
                   (cart_id,)
    )

    items = cursor.fetchall()

    # 組 response
    response = CartResponse(
        user_id = user_id,
        cart_id = cart_id,
        updated_at = datetime.now(timezone.utc)
                     .astimezone(ZoneInfo("Asia/Taipei"))
                     .isoformat(),
        items = [CartItemResponse(
                        menu_item_id=item[0],
                        quantity=item[1]
                        )for item in items
        ]
    )

    conn.commit()

    return response










#----------------------------
# SQLite + Delete Cart
#----------------------------



