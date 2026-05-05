# 李品緯(JasonLee)
# 購物車 API CRUD，包含 post(新增商品)、get(查詢清單所有商品)、delete(刪除商品)、patch(修改商品內容)
# 設計 資料模型 購物車清單()
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

#-----------------
# 模擬 db
#-----------------
cart_db = {} # user_id -> Cart

#--------------------------------------------------------------------------
# 購物車 Internal data Model (負責維護系統邏輯 (統計商品、數量)、(計算最後購買總金額)
#--------------------------------------------------------------------------
# 負責 系統內部邏輯：記錄每個商品、數量、加入時間、更新時間
# 可直接對接資料庫或計算總價、折扣、庫存檢查
# 購物車內商品，購物車只存入
class CartItem(BaseModel):
    menu_item_id: UUID
    quantity: int = Field(gt=0, le=20)
    added_at: datetime

# 購物車主體，也就是顯示所有商品清單
class Cart(BaseModel):
    user_id: int = Field(gt=0)
    items: List[CartItem] = []
    updated_at: datetime

#---------------------Design Request Model---------------------
# API Request / Response Model（業界標準），將責任分離
# 只負責 驗證前端傳入資料 不關心系統內部欄位
# 使用者資料傳入內部不該控制的欄位，發生混合內部邏輯、外部輸入，維護困難
# 未來新增欄位會互相影響(request/response) 兩個不同需求
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
    items: List[CartItemResponse]

class MassageResponse(BaseModel):  # 回傳通知訊息，delete response 204 not content
    massage: str

#--------------------------------------------------------------
# Cart API CRUD
#--------------------------------------------------------------

#--------------------------------------------------------------
# Create
#--------------------------------------------------------------

@app.post("/api/v1/cart/{user_id}/items", status_code=201)
def create_cart_item(user_id: int, data: AddCartItemRequest):
    now = datetime.now()
    if user_id not in cart_db:
        cart_db[user_id] = Cart(user_id=user_id, items=[], updated_at=now)

    cart = cart_db[user_id]

    # 如果購物車存在相同的使用者清單-> 代表商品累加數量
    for item in cart.items:
        if item.menu_item_id == data.menu_item_id:
            item.quantity += data.quantity
            item.added_at = now
            return {"massage":"餐點數量已更新"}

    cart.items.append(CartItem(menu_item_id=data.menu_item_id,quantity=data.quantity,added_at=now))
    cart.updated_at = now
    return {"massage":"餐點已加入至購物車"}

#--------------------------------------------------------------
# Get
#--------------------------------------------------------------

@app.get("/api/v1/cart/{user_id}/",response_model=CartResponse,status_code=200)
def get_user_cart(user_id: int):
    if user_id not in cart_db:
        raise HTTPException(status_code=404,detail="Cart not found")

    cart = cart_db[user_id]
    user_cart = CartResponse(user_id=cart.user_id,
                             items=[CartItemResponse(
                                        menu_item_id=c.menu_item_id,
                                        quantity=c.quantity)for c in cart.items]
                             )
    return user_cart

#--------------------------------------------------------------
# Delete 產品
#--------------------------------------------------------------

@app.delete("/api/v1/cart/{user_id}/items/{menu_item_id}/",status_code=204)
def delete_cart_item(user_id: int, menu_item_id: UUID):
    now = datetime.now()
    if user_id not in cart_db:
        raise HTTPException(status_code=404,detail="Cart not found")

    # 查詢購物車，把同樣id 餐點過濾掉，只留不同的餐點變成新的購物車清單
    # 當遇到要刪除列表裡面多筆的資料時，可以用條件過濾的方式當作刪除，
    # 內建的函數沒有刪除多筆方法，向delete(只能刪除1筆但是要知道index)、re-move(要知道位置，也只能珊一筆)
    # 整理以上內容: 列表生成式 把不符合條件保留，符合條件過濾(刪除),在生成一個新列表
    cart = cart_db[user_id]
    new_items = [item for item in cart.items if item.menu_item_id != menu_item_id]

    # 檢查過濾完後的購物車與沒過濾前購物車資料是否長度一樣
    if len(new_items) == len(cart.items):
        raise HTTPException(status_code=404,detail="Item not found")
    cart.items = new_items
    cart.updated_at = now
    return

#--------------------------------------------------------------
# Patch 產品
#--------------------------------------------------------------

@app.patch("/api/v1/cart/{user_id}/items/{menu_item_id}",status_code=200)
def update_item(user_id: int, menu_item_id: UUID, data: UpdateCartItemRequest):

    if user_id not in cart_db: # 檢查這個使用者有沒有購物車？
        raise HTTPException(status_code=404, detail="Cart not found")

    cart = cart_db[user_id]

    # 清空購物車不存在的商品，查詢商品修改商品數量
    for item in cart.items:
        if item.menu_item_id == menu_item_id: # 比對商品id
            if data.quantity == 0:  # quantity = 0 → 刪除
                cart.items.remove(item)
                cart.updated_at = datetime.now()
                return {"message": "item removed"}
            elif data.quantity is not None:
                item.quantity = data.quantity
                cart.updated_at = datetime.now()
                return {"message": "item updated"}

    # 針對購物車裡面有沒有這個商品,防止假成功
    raise HTTPException(status_code=404, detail="Item not found")
