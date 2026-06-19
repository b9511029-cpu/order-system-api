# 李品緯(JasonLee)
# api.py , 用途 建立一個 API 統一入口(關鍵),讓 main.py 變乾淨
# 未來加入API,不用動 main.py
# 可以做 versioning(v1/v2)
from fastapi import APIRouter
from routes import user, menu, cart, order

print("order router loaded")
# 建立統一入口
api_router = APIRouter()

# 組合路徑
api_router.include_router(user.router)
api_router.include_router(menu.router)
api_router.include_router(cart.router)
api_router.include_router(order.router)