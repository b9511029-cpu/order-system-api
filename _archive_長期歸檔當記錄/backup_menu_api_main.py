# 李品緯(JasonLee)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"], # 允許所有來源
    allow_methods=["*"],      # 允許所有 HTTP 方法
    allow_headers=["*"],      # 允許所有 headers
)

# 建立餐點模型
class MenuItem(BaseModel):
    id: int = Field(ge=1,le=100)
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

# 記憶體資料庫 模擬測試
menu_db: dict[int, MenuItem] = {} # 資料庫改成字典

# old API
# -------------------新增(POST)-------------------------
@app.post("/api/v1/menu/",
          response_model=MenuItem,status_code=201)
def create(item: MenuItem):
    if item.id in menu_db:
        raise HTTPException(status_code=400,
                            detail="ID already exists")
    menu_db[item.id] = item
    return item

# -------------------查詢(GET)--------------------------
@app.get("/api/v1/menu/",
         response_model=list[MenuItem],status_code=200)
def get_list_all():
    return list(menu_db.values()) # 取得資料的值(value),放入列表回傳


# -------------------查詢(GET)單一資料--------------------------
@app.get("/api/v1/menu/{item_id}",
         response_model=MenuItem,status_code=200)
def get_single_menu_item(item_id: int):
    if item_id not in menu_db:
        raise HTTPException(status_code=404,
                            detail=f"item not found {item_id}不存在")
    return menu_db[item_id]


# ------------------更新(整 筆 覆 蓋 PUT)------------------
@app.put("/api/v1/menu/{item_id}", status_code=200)
def update_all_item(item_id: int, item: MenuItem):
    print("call patch ok")
    if item_id not in menu_db:
        raise HTTPException(status_code=404, detail="Item not found")
    if item_id != item.id:
        raise HTTPException(status_code=400,
                            detail="item_id 與 item.id 不匹配")

    menu_db[item_id] = item
    return item

# -------------------更新(局部覆蓋 PATCH )-----------------
# 因為patch 多設計一個patch 專用的資料模型 MenuItemUpdate
# 因為原本MenuItem不適合patch使用，因為name、price、都是必要的資料，不能夠改option
# 因此需要將API修正成(Refactor)正確架構，不算亂改main.py，這叫正確的架構調整

@app.patch("/api/v1/menu/{item_id}",
           status_code=200,response_model=MenuItem)
def update_patch_item(item_id: int, item: MenuItemUpdate): # 更改參數型別
    if item_id not in menu_db:
        raise HTTPException(status_code=404,
                            detail="Item not found")
    # 局部修改
    stored_item = menu_db[item_id] # 資料庫的原始資料
    updated = item.model_dump(exclude_unset=True) # 更新欄位轉換成json
    updated_item = stored_item.model_copy(update=updated) # 更新指定欄位
    menu_db[item_id] = updated_item # 建立更新的欄位物件
    return updated_item
# model_dump() 把pydantic 模型物件轉成 python dict
# exclude_unset = True 只接收 資料模型真實有傳值的資料，排除沒有值或者None的欄位

# -------------------刪除(delete)-------------------------
@app.delete("/api/v1/menu/{item_id}",status_code=204)
def delete_item(item_id: int):
    if item_id not in menu_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del menu_db[item_id]
    # 不返回內容