# 李品緯(JasonLee)
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from API作品.db.database import get_db
from API作品.repositories.cart_repository import CartRepository

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"], # 允許所有來源
    allow_methods=["*"],      # 允許所有 HTTP 方法
    allow_headers=["*"],      # 允許所有 headers
)

now = datetime.now()
print("Reload",now.isoformat())

#---------------------------
# 購物車 Internal data Model
#---------------------------

class CartItem(BaseModel):
    id: UUID
    menu_item_id: UUID
    quantity: int = Field(gt=0, le=20)
    added_at: datetime

class Cart(BaseModel):
    id: UUID
    user_id: int = Field(gt=0)
    items: List[CartItem] = Field(default_factory=list)
    updated_at: datetime

#---------------------------------------------------
# Apply Front User Request Models (負責新增、驗證資料)
#---------------------------------------------------
class AddCartItemRequest(BaseModel):
    menu_item_id: UUID
    quantity: int = Field(gt=0,le=20)
#-------------------------------------
# update(patch) Models (負責更改產品數量)
#-------------------------------------
class UpdateCartItemRequest(BaseModel):
    quantity: int | None = Field(default=None, ge=0)

#--------------------------------------------------------------
# Response Front User update Cart data Models (負責回應前端結果)
#--------------------------------------------------------------
class CartItemResponse(BaseModel):
    menu_item_id: UUID
    quantity: int

class CartResponse(BaseModel):
    user_id: int
    cart_id: UUID
    updated_at: str
    items: List[CartItemResponse]

class MessageResponse(BaseModel):
    massage: str


#----------------------------
# SQLite + Add Cart
#----------------------------

@app.post("/api/v2/cart/{user_id}/items",status_code=201,response_model=CartResponse)
def add_to_cart(user_id: int, data: AddCartItemRequest,conn=Depends(get_db)):
    # 建立時間
    now_taipei = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Taipei")).isoformat()

    cart_repo = CartRepository(conn)

    cart_row = cart_repo.get_cart_rows_by_user_id(user_id=user_id)

    if cart_row is None:
        # cart exist -> Keep use
        cart_id = cart_repo.create_a_new_cart(user_id=user_id,now_time=now_taipei)

        is_new_cart = True # flag (標記),用來標記，物件是不是剛剛建立的
    else:
        cart_id = cart_row['id']

        is_new_cart = False

    # 確認 quantity 不是空值
    existing_quantity = cart_repo.check_cart_item_quantity(cart_id=cart_id, meal_id=data.menu_item_id)

    if existing_quantity is not None:
        current_quantity = existing_quantity['quantity'] # 取得 dict 對應的數值

        # ***加入累加後超過上限檢查 [Guard Clause（防衛式寫法）]
        if current_quantity + data.quantity > 20: # 累加結果 > 20 會執行raise 中斷
            raise HTTPException(status_code=400,detail="Total quantity cannot exceed 20")

        cart_repo.cart_item_accumulation_quantity(quantity=data.quantity, cart_id=cart_id, meal_id=data.menu_item_id)

    # 無數量欄位，代表要加入新的商品
    else:
    # 建立購物車最後更新時間
        ci_id = uuid4()
        cart_repo.add_new_cart_item_to_cart(ci_id=ci_id,
                                            orig_cid=cart_id,
                                            req_menu_id=data.menu_item_id,
                                            req_quantity=data.quantity,
                                            now_time=now_taipei)

    # 查出最新 items
    cart_repo.add_the_cart_updated_at_time(now_time=now_taipei,
                                           orig_cid=cart_id)

    items = cart_repo.get_now_cart_items_by_cart_id(c_id=cart_id)

    final_cart = (
        CartResponse(
            user_id = user_id,
            cart_id = cart_id,
            updated_at= now_taipei,
            items =[CartItemResponse(
                menu_item_id=i['menu_item_id'],
                quantity=i['quantity']
                ) for i in items]
            )
    )
    return final_cart

#----------------------------
# SQLite + Get Cart + 測試框架
#----------------------------
@app.get("/api/v2/cart/{user_id}",response_model=CartResponse)
def get_cart(user_id: int,conn=Depends(get_db)):

    cart_repo = CartRepository(conn)

    cart_rows = cart_repo.get_cart_rows_by_user_id(user_id)

    if cart_rows is None:
        raise HTTPException(status_code=404, detail="cart not found")

    # Supply (cart_id, updated_at)
    cart_id , updated_at = cart_rows # unpacking (解構/結構對應)

    cart_item_rows = cart_repo.get_now_cart_items_by_cart_id(c_id=cart_id)

    cart_response = CartResponse(
        user_id = user_id,
        cart_id = cart_id,
        updated_at = updated_at,
        items = [
            CartItemResponse(
                menu_item_id = menu_item_id,
                quantity = quantity
            )
            for menu_item_id, quantity in cart_item_rows # tuple unpacking (解構/結構對應)
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
    cart_repo = CartRepository(conn)

    c_id = cart_repo.get_the_cart_id_by_user_id(user_id=user_id)

    # 判斷是否購物車是否存在
    if c_id is None:
        raise HTTPException(status_code=404, detail="cart not found")

    cart_id = c_id['id']  # dict unpacking

    ci_item = cart_repo.check_cart_item_quantity(cart_id=cart_id, meal_id=menu_item_id)

    if ci_item is None:
        raise HTTPException(status_code=404, detail="cart items not found")

    #　更新
    new_qty = data.quantity

    if new_qty > 20:
        raise HTTPException(status_code=400, detail="quantity cannot be greater than 20")

    if new_qty == 0:

        cart_repo.delete_cart_items_by_cart_id_and_menu_item_id(cart_id=cart_id, meal_id=menu_item_id)

    else:

        cart_repo.update_cart_item_quantity(qty=new_qty, c_id=cart_id, m_i_id=menu_item_id)


    ci_items = cart_repo.get_now_cart_items_by_cart_id(c_id=cart_id)

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
                        )for item in ci_items
        ]
    )

    return response

#----------------------------
# SQLite + Delete Cart
#----------------------------
@app.delete("/api/v2/cart/{user_id}/items/{menu_item_id}",response_model=CartResponse)
def delete_cart_item(user_id: int, menu_item_id: UUID,conn=Depends(get_db)):

    cart_repo = CartRepository(conn)

    db_cid = cart_repo.get_the_cart_id_by_user_id(user_id = user_id)

    if db_cid is None:
        raise HTTPException(status_code=404, detail="cart not found")

    cart_id = db_cid['id']

    ci_rows = cart_repo.get_menu_item_id_and_quantity_by_cid_and_mid(cart_id=cart_id,
                                                                     meal_id=menu_item_id)

    if not ci_rows:

        raise HTTPException(status_code=404, detail="item not found")

    cart_repo.delete_cart_items_by_cart_id_and_menu_item_id(cart_id=cart_id,
                                                            meal_id=menu_item_id)

    ci_items = cart_repo.get_menu_item_id_and_quantity_by_cid_and_mid(cart_id=cart_id,
                                                                      meal_id=menu_item_id)

    response = CartResponse(
        user_id = user_id,
        cart_id =cart_id,
        updated_at = datetime.now(timezone.utc)
                    .astimezone(ZoneInfo("Asia/Taipei"))
                    .isoformat(),
        items = [CartItemResponse(
                        menu_item_id = menu_item_id,
                        quantity= quantity
                    )for menu_item_id, quantity in ci_items
                 ]
        )

    return response






