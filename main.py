# 李品緯(JasonLee)
# modular API architecture（模組化架構）
from fastapi import FastAPI
from routes.api import api_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware, # type: ignore
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routers
app.include_router(api_router, prefix="/api/v1")

# 沒有首頁，充當首頁的 router
@app.get("/")
def root():
    return {"message": "API is running"}


