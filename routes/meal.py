# 李品緯(JasonLee)
from datetime import datetime
from typing import List
from uuid import UUID
from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel, Field
from db.database import get_db
from repositories.meal_repository import MealRepository

router = APIRouter(prefix="/menu")

print(f"meal 載入時間:{datetime.now().isoformat()}")

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


@router.post("/", response_model=MenuItem, status_code=201)
def create_menu_item(item: MenuItem,conn=Depends(get_db)):

    meal_repo = MealRepository(conn)

    meal_id = meal_repo.get_meal_id_by_id(item.id)

    if meal_id:
        raise HTTPException(status_code=409,detail="ID already exists")

    meal_repo.create_meal_data(item.id,
                               item.name,
                               item.price,
                               item.description,
                               item.image_url)
    return item

# ----------------------menu_db_Get all--------------------------
@router.get("/", response_model=List[MenuItem])
def get_menu_all(conn=Depends(get_db)):

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
@router.get("/{item_id}", response_model=MenuItem, status_code=200)
def get_single_menu_item(item_id: UUID,conn=Depends(get_db)):

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
@router.put("/{item_id}", status_code=200)
def update_all_item(item_id: UUID, update_item: MenuItem,conn=Depends(get_db)):
    # id 必須一致
    if item_id != update_item.id:
        raise HTTPException(status_code=400,
                            detail="item_id 與 item.id 不匹配")

    meal_repo = MealRepository(conn)

    meal_id = meal_repo.get_meal_id_by_id(item_id)

    if meal_id is None:
        raise HTTPException(status_code=404, detail="Item not found")

    meal_repo.update_meal_all_data(name=update_item.name,
                                   price=update_item.price,
                                   description=update_item.description,
                                   image_url=update_item.image_url,
                                   item_id=item_id
                                   )
    return update_item

# -------------------------------PATCH 更新 API-------------------------------
@router.patch("/{item_id}", response_model=MenuItem)
def update_patch_item(item_id: UUID, item: MenuItemUpdate = ..., conn=Depends(get_db)):

    meal_repo = MealRepository(conn)

    stored_item = meal_repo.find_meal_by_id(item_id)

    if not stored_item:

        raise HTTPException(status_code=404, detail="Item not found")

    # 將資料模型 轉換成 字典(key,value)
    # item.dict(exclude_unset=True):V2.過時版本,現在業界實務做法 model_dump(),完全向後兼容 Pydantic v2 的新 API
    # 只抓使用者在 PATCH 中實際傳入的欄位,沒有傳的欄位不會包含在 dict 裡
    update_field = item.model_dump(exclude_unset=True)

    if not update_field:

        raise HTTPException(status_code=400, detail="未提供更新欄位的資料")

    # 取得更新後的資料
    meal_repo.update_meal_fields(item_id, update_field)

    updated_meal = meal_repo.find_meal_by_id(item_id)

    # ** = 字典解包成 關鍵字參數，把 dict 直接傳給 Pydantic
    # 模型或函數,轉成 MenuItem 模型，方便回傳給前端
    return MenuItem(**dict(updated_meal))

# -------------------刪除(delete)-------------------------
@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: UUID,conn=Depends(get_db)):

    meal_repo = MealRepository(conn)

    stored_item = meal_repo.find_meal_by_id(item_id)

    if not stored_item:

        raise HTTPException(status_code=404, detail=f"Item not found")

    meal_repo.delete_meal_by_id(item_id)

    return # 204

