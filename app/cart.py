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

    # cursor = conn.cursor()
    # cursor.execute("SELECT id FROM carts WHERE user_id = ?",(user_id,))
    # row = cursor.fetchone()
    cart_repo = CartRepository(conn)
    cart_row = cart_repo.get_cart_by_user_id(user_id=user_id)
    print("cart_row",cart_row)
    if cart_row is None:

        # cart_id = str(uuid4())
        # cursor.execute("INSERT INTO carts (id, user_id, updated_at) VALUES(?,?,?)",
        #                (cart_id,user_id,now_taipei)
        #                )

    # cart exist -> Keep use
        cart_repo.create_a_new_cart(user_id=user_id,now_time=now_taipei)

    else:
        originally_cid = cart_row[0]

    # 更改購物車商品數量，查詢購物車資料表欄位
    # cursor.execute("""SELECT quantity FROM cart_items
    #                       WHERE cart_id = ? AND menu_item_id = ? """,
    #                 (cart_id, str(data.menu_item_id))
    # )
    # # pick DB quantity value
    # existing_quantity = cursor.fetchone()


    # 確認 quantity 不是空值
    existing_quantity = cart_repo.check_cart_item_quantity(cart_id=originally_cid, data=data.menu_item_id)

    if existing_quantity is not None:
        current_quantity = existing_quantity[0] # 取得tuple 中的數值

        # ***加入累加後超過上限檢查 [Guard Clause（防衛式寫法）]
        if current_quantity + data.quantity > 20: # 累加結果 > 20 會執行raise 中斷
            raise HTTPException(status_code=400,detail="Total quantity cannot exceed 20")

        # 當累加結果<20，沒有執行raise 會自然執行 更改數量
        # cursor.execute("""UPDATE cart_items SET quantity = quantity + ?
        #                       WHERE cart_id = ? AND menu_item_id = ? """,
        #                (data.quantity, cart_id, str(data.menu_item_id))
        #                 )
        cart_repo.update_cart_item_quantity(cart_id=originally_cid, request=data)


    # 無數量欄位，代表要加入新的商品
    else:
        # cursor.execute("""
        #                     INSERT INTO cart_items (id, cart_id, menu_item_id, quantity, added_at)
        #                     VALUES (? ,? ,? ,?,? ) """,
        #                (
        #                     str(uuid4()),
        #                     originally_cid,
        #                     str(data.menu_item_id),
        #                     data.quantity,
        #                     now_taipei
        #                )
        # )

    # 建立購物車最後更新時間
        ci_id = uuid4()
        cart_repo.add_new_cart_item_to_cart(ci_id=ci_id,
                                            orig_cid=originally_cid,
                                            req_menu_id=data.menu_item_id,
                                            req_quantity=data.quantity,
                                            now_time=now_taipei)



    # cursor.execute("UPDATE carts SET updated_at = ? WHERE id = ? ",
    #                (now_taipei, originally_cid))

    # 查出最新 items
    cart_repo.add_the_cart_updated_at_time(now_time=now_taipei,
                                           orig_cid=originally_cid)

    # cursor.execute("""SELECT menu_item_id,quantity FROM cart_items
    #                       WHERE cart_id = ? """,
    #                (originally_cid,)
    # )
    #items = cursor.fetchall()
    items = cart_repo.get_cart_items_by_cart_id(c_id=originally_cid)


    final_cart = (
        CartResponse(
            user_id = user_id,
            cart_id = originally_cid,
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

    # cursor = conn.cursor()
    # cursor.execute("SELECT id, updated_at FROM carts WHERE user_id = ?"
    #                ,(user_id,))
    # c_row = cursor.fetchone()
    cart_repo = CartRepository(conn)

    cart_rows = cart_repo.get_cart_by_user_id(user_id)

    if cart_rows is None:
        raise HTTPException(status_code=404, detail="cart not found")

    # Supply (cart_id, updated_at)
    cart_id , updated_at = cart_rows # tuple unpacking (解構/結構對應)

    # cursor.execute("SELECT menu_item_id, quantity FROM cart_items WHERE cart_id = ?"
    #                ,(cart_id,))
    #
    # ci_rows = cursor.fetchall()
    cart_item_rows = cart_repo.get_cart_items_by_cart_id(c_id=cart_id)

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
@app.delete("/api/v2/cart/{user_id}/items/{menu_item_id}",response_model=CartResponse)
def delete_cart_item(user_id: int, menu_item_id: UUID,conn=Depends(get_db)):

    cursor = conn.cursor()

    cursor.execute("SELECT id FROM carts WHERE user_id = ?",(user_id,))

    c_row = cursor.fetchone()

    if c_row is None:
        raise HTTPException(status_code=404, detail="cart not found")

    cart_id = c_row[0]

    cursor.execute("SELECT menu_item_id, quantity FROM cart_items "
                   "WHERE cart_id = ? AND menu_item_id = ?",
                   (cart_id, str(menu_item_id))
                   )

    ci_row = cursor.fetchall()

    if not ci_row:

        raise HTTPException(status_code=404, detail="item not found")

    cursor.execute("DELETE FROM cart_items WHERE cart_id = ? AND menu_item_id = ?",
                   (cart_id,str(menu_item_id))
                   )
    conn.commit()


    cursor.execute(""" SELECT menu_item_id, quantity FROM cart_items 
                           WHERE cart_id = ? AND menu_item_id = ? """,
                   (cart_id,str(menu_item_id)))

    items = cursor.fetchall()



    response = CartResponse(
        user_id = user_id,
        cart_id =cart_id,
        updated_at = datetime.now(timezone.utc)
                    .astimezone(ZoneInfo("Asia/Taipei"))
                    .isoformat(),
        items = [CartItemResponse(
                        menu_item_id = menu_item_id,
                        quantity= quantity
                    )for menu_item_id, quantity in items
                 ]
        )

    return response






