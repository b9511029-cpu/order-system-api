# 線上點餐系統 order system

一個模擬餐廳點餐流程的後端專案，包含前台點餐與後台訂單管理，
重點在於實作完整 CRUD 流程與未來前後端整合


---

## 專案亮點

 - 完整訂單流程(點餐 ok->購物車 ok->建立訂單(未來繼續完成)->狀態更新(未來繼續完成))
 - 前後端分離架構 （RESTful API）
 - 使用JWT 做登入驗證 (未來繼續完成)
 - 後臺管理系統 (餐點 ok / 訂單 CRUD (未來繼續完成)) 
 - 狀態管理 (例如: 購物車 ok / 訂單狀態 (未來繼續完成))

---

## 技術棧

- Frontend：VS code
- Backend：Python/FastAPI
- Database：Python.sqlite3
- 其他：HTML/Bootstrap/Pytest/
- API 文件: Swagger

---

## 系統功能

### 使用者
- 瀏覽菜單
- 加入購物車
- 建立訂單

### 管理者
- 管理餐點（新增 / 編輯 / 刪除）
- 更新訂單狀態

---

## 技術重點說明

- 使用 RESTful API 設計前後端溝通
- JWT 實作登入驗證與權限控管 (未來繼續完成)
- 將購物車資料存在前端 state 並同步後端
- 訂單狀態設計（pending / processing / done）(未來繼續完成)

---