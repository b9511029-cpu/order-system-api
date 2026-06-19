# 李品緯(JasonLee)
from datetime import datetime
from typing import List
from uuid import UUID, uuid4
from enum import Enum
from fastapi import APIRouter
from fastapi.params import Depends
from pydantic import BaseModel, Field
from db.database import get_db
from db.init_db import cursor
from repositories.cart_repository import CartRepository
from repositories.meal_repository import MealRepository


# router = APIRouter(prefix="/order", tags=["order"])
router = APIRouter(prefix="/order", tags=["order"])

print("order 載入時間", datetime.now().isoformat())

# 列舉出定義好的字串，交給 order.Basemodel 去驗證
class OrderStatus(str, Enum):
    pending = "pending"
    complete = "complete"
    cancelled = "cancelled"

class OrderItem(BaseModel):
    menu_item_id: UUID
    menu_name: str
    unit_price: int = Field(ge=0)
    quantity: int = Field(ge=0)

# 以上，建立 Order Schema
class Order(BaseModel):
    id: UUID
    user_id: int = Field(ge=0)
    total_amount: int = Field(ge=0)
    status: OrderStatus
    created_at: datetime
    items: List[OrderItem]

# 查詢 訂單要回傳資料
class OrderResponse(BaseModel):
    id: UUID
    total_amount: int
    status: OrderStatus
    created_at: str

class OrderDetailResponse(BaseModel):
    id: UUID
    user_id: int
    total_amount: int
    status: OrderStatus
    created_at: str
    items: List[OrderItem]


@router.post("/", status_code=201)
def create_order(user_id: int,conn=Depends(get_db)):

    cart_repo = CartRepository(conn)
    menu_repo = MealRepository(conn)

    # 1. 找到使用者的購物車
    cart = cart_repo.get_the_cart_id_by_user_id(user_id=user_id)

    # 2. 檢查購物車是否為空
    if not cart:
        raise ValueError("Cart not found")

    cart_id = cart["id"]
    # print("cart_id", cart_id)

    # 3. 取得購物車商品
    cart_items = cart_repo.get_now_cart_items_by_cart_id(c_id=cart_id)

    # print("cart_items", cart_items)

    if not cart_items:
        raise ValueError("Cart is empty")

    # 4. 算計總價
    total_amount = 0

    for item in cart_items:

        menu_item_id = item["menu_item_id"]
        quantity = item["quantity"]

        meal = menu_repo.get_meal_by_id(meal_id=menu_item_id)

        if not meal:
            raise ValueError("Meal not found")

        unit_price = meal["price"]

        total_amount += unit_price * quantity

    # 5. 建立 Order
    order_id = str(uuid4())
    created_at = datetime.now().isoformat()
    status = OrderStatus.pending

    cursor.execute("""
        INSERT INTO orders (id, user_id, total_amount, status, created_at) 
        VALUES (?,?,?,?,?)
    """,(order_id, user_id, total_amount, status, created_at))

    # 6. 建立 OrderItem
    for item in cart_items:

        menu_item_id = item["menu_item_id"]
        quantity = item["quantity"]

        meal = menu_repo.get_meal_by_id(meal_id=menu_item_id)

        order_item_id = str(uuid4())

        cursor.execute("""
            INSERT INTO order_items (id, order_id, 
                                     menu_item_id, 
                                     menu_name, 
                                     unit_price, 
                                     quantity)
                                     VALUES (?,?,?,?,?,?) """
                                    ,(order_item_id,
                                      order_id,
                                      menu_item_id,
                                      meal["name"],
                                      meal["price"],
                                      quantity)
                       )

    # 7. 清空購物車
    cart_repo.clear_cart_items(cart_id=cart_id)

    cursor.commit()

    return order_id






router.get("/orders", status_code=200)
def get_orders():
    pass

router.get("/order/{order_id}", status_code=200)
def get_order(order_id: UUID):
    pass

router.patch("/order/{order_id}/cancel", status_code=200)
def cancel_order(order_id: UUID):
    pass









