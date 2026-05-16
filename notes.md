

-----------------------------------------------

# 購物車 開發筆記/Debug 紀錄

-----------------------------------------------

Q1: 測試 post 過程中
Then: 回傳成功
assert res1.status_code == 201
data = res1.json()
assert len(data["items"]) == 1
#### assert data["items"][0]["quantity"] == 1 (NG)
1.驗證時需要準確知道索引位置，加上可讀性不好。 
2.list 會有 index 順序性問題，當 quantity=0 ,index 會報錯。
#### item = next(i for i in data["items"] if i["menu_item_id"] == menu_item_id) (OK)
改成生成器表達式確保驗證的是正確商品，不依賴 list 順序性
assert item["quantity"] == 1

### 生成器表達式 → 我要從一堆資料裡找第一個符合條件的元素
item = next(i for i in data["items"] if i["menu_item_id"] == menu_item_id)
透過for/in loop 讀取符合第一個條件的元素，進行比對編號保證驗證是正確的資料
(在資料比對上比較準確)

next() -> 一個一個取出來
從 迭代器（iterator）（像 list、tuple、generator）拿下一個值的內建函式

適合像購物車API 測試以下這類型資料 data = res1.json()
data["items"] = [
{"menu_item_id": "...", "quantity": 1},
{"menu_item_id": "...", "quantity": 3},
] 

解決:
1. 可讀性更佳
2. 驗證資料準確性 比 list 更好
3. 預防未來潛在性錯誤

---

Q2: 測試 post 邏輯累加數量邊界測試
    
def test_add_same_item_with_accumulation_exceeding_mix_quantity_should_fail():
   # Given: 新增使用者與商品
   user_id = 11
   menu_item_id = str(uuid4())
   # When: 使用者傳入累加數量
   client.post(f"/api/v2/cart/{user_id}/items/",
               json={
                   "menu_item_id": menu_item_id,
                   "quantity": 15
               }
   )
   res_2= client.post(f"/api/v2/cart/{user_id}/items/",
                     json={
                       "menu_item_id": menu_item_id,
                       "quantity": 6
                     }
   )
   # Then: 回應驗證錯誤
   assert res_2.status_code == 400 # bad request(請求不符合業務規則)

累加數量超過上限20,不能是422,驗證欄位與類型有效執錯誤
累加數字符合欄位限制，這是屬於累加後邏輯錯誤，通常由400/409比較合適
不選409 比較偏向操作跟目前系統狀態衝突(DB) 

# error msg 
E       assert 201 == 400
E        +  where 201 = <Response [201 Created]>.status_code
ex76test_v2.py:268: AssertionError

# 解決辦法: 修整API 驗證錯誤 (累加狀態一定需要加一條業務邏輯處理累加上限檢查)
***加入累加超過上限檢查 [Guard Clause（防衛式寫法）
if current_quantity + data.quantity > 20: # 累加結果 > 20 會執行raise 中斷
    raise HTTPException(status_code=400,detail="Total quantity cannot exceed 20")

---
Q3: 測試 給錯商品編號 讓刪除商品失敗時(item not found)
error 1 : 當查詢時未給 商品編號 變數(str(menu_item_id))),所以結果永遠都是空購物車
error 2 : 設計上觀念錯誤 [] 不等於是 None 造成條件不成立 

cursor.execute("SELECT menu_item_id, quantity FROM cart_items "
                   "WHERE cart_id = ? AND menu_item_id = ?",
                   (cart_id, str(menu_item_id)))

    ci_row = cursor.fetchall() # 輸出是空 [] 
                                # python 認為 [] 不等於 None, 所以 if 永遠不成立

    if ci_row is None:
        print("404 execute item")
        raise HTTPException(status_code=404, detail="item not found")

解決辦法: 將 if 改為 if not ci_row (業界常用寫法) , 原因: 在 python [] 視為 false
        結果: if not ci_row -> if True 成立 raise 404 error

---


---
# 購物車刪除 設計想法
Delete: 直接刪除資源,本質就是 消失
Q1: DELETE 你要刪的是哪一層？ item

Q2: DELETE 的「流程是什麼？
delete flow : 找 cart → 找 item → 刪掉那一筆 → 回傳cart 本質是「消失」
-> 直接移除資源

Q3: DELETE 成功後要回什麼？ 回更新過後的cart

Q4: DELETE 的錯誤怎麼處理？
1.cart 不存在  404 cart not found
2.item 不存在  404 item not found

Q5: DELETE 跟 PATCH 差在哪？
PATCH : 改狀態 (update quantity)
DELETE : 移除資料 (remove row)

Q6: （設計陷阱）
PATCH 已經有： quantity = 0 → delete item (原因:業務刪除（語意）)
DELETE 還要存在嗎？ 要 資源被移除 (原因:REST 刪除（語意）)
#### 兩個是不同層級語意

Q7: DELETE 測試你要怎麼想？
1. 正常刪除 ->item 存在 → 刪掉 → items 少一個
2. item 不存在-> 404
3. cart 不存在-> 404
patch flow :找 cart → 找 item → 改 quantity → 回傳cart 本質是「狀態變更」
->改數量 / 刪掉 item（quantity = 0）

delete flow:
                user_id → cart
                        ↓
                    menu_item
                        ↓
                    delete row
                        ↓
                return updated cart








-----------------------------------------------

# 使用者 開發筆記/Debug 紀錄

-----------------------------------------------


-----------------------------------------------

# 餐點 開發筆記/Debug 紀錄

-----------------------------------------------


-----------------------------------------------
# 開始拆分 檔案 職責

#  解決 資料庫 分散問題 紀錄
建立多個 API ，分散式的資料庫無法建立關聯與後續難以管理
需集中 TABLES 連到共享的資料庫 "app.db"
讓資料庫形成一個共同儲存空間，這就是 關聯設計(relational design),這樣也是一個共享資料庫的 Core Entity(核心實體)
所以要建立一個database 相關架構 將.db/conn/schema.sql 獨自建立出來 

API_project/
│
├── app/
│   ├── cart.py         # 代表 API endpoint , 這裡會改成路由/入口端點
│   ├── meal.py
│   └── user.py
│
├── db/
│   ├── app.db          # 代表 restaurant.db 儲存庫
│   ├── init_db.py      # 代表 負責建立 table , 只會跑一次,設定 外鍵 ON , 預設是 OFF
│   └── database.py     # 代表 負責 DB connection 例如:get_db_connection() , 用途:未來API 會一職使用這個連線
│
├── test/
│
└── main.py

#### 專案調整上的誤解
app/
└── app.db   ❌ API 會被呼染、容易跟code混再一起、之後要換資料庫很難

users.db
meals.db
cart.db   ❌ 資料分裂 無法Join 不符合資料庫設計，資料需要是統一集中管理,方便給整個專案使用 (DB 應該是「全專案共享一個」)

在開發階段 常常容易會把資料、連線、API 邏輯全部寫在同一個.py，因此後續維護時會很困難
但是開發時期，需要經常測試API 功能與流程的完整性，這是專案必要過程

#### init_db.py 建立一個app.db,連線部分後續會再拆分出來獨立
init_db.py 先用sqlite3.connnect DB 建立 table 並立馬設定 外鍵ON(Foreign key)
(推薦)
conn = sqlite3.connect("restaurant.db")
conn.execute("PRAGMA foreign_keys = ON") # foreign key 是屬於connect status
(foreign key 是屬於連線狀態中開啟，而不是執行操作狀態下開啟)
❌ cursor.execute("PRAGMA foreign_keys = ON")

補充一個觀念，購物車本身是一個狀態，並無生命週期，
所謂生命週期指的是有資料長期保存的實體(user/menu/cart_items/order_items)

#### 測試 DB schema (模式)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
# print("name FROM:",cursor.fetchall()) 測試 Create TABLE OK

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
# print("sql FROM:",cursor.fetchall())  檢查欄位設計 OK

try:  # 測試 Foreign key 生效
    cursor.execute("""
    INSERT INTO cart_items (id, user_id, menu_id, quantity, added_at)
    VALUES (?, ?, ?, ?, ?)
    """, ("test", 999, "xxx", 1, "2026-01-01"))

    conn.commit()

except Exception as e:
    print("FK test failed:", e)

try: # UNIQUE constraint 生效
    cursor.execute("""
                   INSERT INTO users (id, user_name, email, password, created_at) 
                   VALUES (?,?,?,?,?)
                    """,
                   (1,"test","test@email.com",'123', "2026-01-01")
    )
    cursor.execute("""
                    INSERT INTO menus (id, name, price) 
                    VALUES (?,?,?)
                    """
                   ,("m1", "burger", 100)
    )
    cursor.execute("""
                    INSERT INTO cart_items (id, user_id, menu_id, quantity, added_at)
                    VALUES (?,?,?,?,?)"""
                   ,("c2", 1, "m1", 1, "2026-01-01")
    )
except Exception as e:
    print("你的 UNIQUE constraint 生效了->",e)

#### DB 完成 schema test 雖然有更動 cart_id / menu_item_id
#### 但接下來，測 cart business logic 時，邊測邊修 API 直到對齊 DB schema
這種屬於重要的工程概念
真正開發時，先穩定 DB schema , 然後再慢慢調整API (在開發測試階段 很正常)
所謂實際工程流程: Interactive Refactoring(迭代式重購)

#### 建立 database.py , 建立連線模組

路徑本身就不屬於API,DB PATH 遷移到 database.py 可以建立所有API 通一路徑
DB_PATH 本身只是用來定位檔案位置，沒有任何連線/傳輸用途

def get_db_connection():
    conn = sqlite3.connect("app.db")
    conn.execute("PRAGMA foreign_keys = ON")
 ***conn.row_factory = sqlite3.Row 　
    return conn

database.py 正確流程
API
  ↓ --> database.py
get_db_connection()
  ↓
sqlite3.connect(DB_PATH)
  ↓
SQLite 引擎
  ↓
執行 SQL
  ↓
回傳結果給 API

預先設定讀取格式  
連線程式 預先設定 當 connect 接收 python 執行查詢 sqlit3 回傳資料(tuple)
因預設取值方式，先透過 sqlite3.Row 物件 轉換格式後(row["name"]), python 才會接收

-----------------------------------------------

# 連線與資料庫 已拆分出去，進行 API Refactor content
# 透過API 測試流程 邊測試邊調整API (迭代式重構)

購物車未完成 API 重構測試，執行 post 發現 cart 改成 cart_items 但是 插入值時 因為cart and cart_item 參數有少
後來發現當初 carts API 將 carts and cart_items 做了混和邏輯，
因為發現說 cart 在有order 系統中才能有作用， carts 屬於暫存狀態(無生命週期) 適合拿來當 order_的快照資料，
所以後來才打算 init_db.py 不建立 cart table ，後來測試 API flow 發現無法測試 , 因為會動到 cart API business logic
所以才重新再init_db.py 建立 cart table

user/meal/cart API and 跌代重構 已測試完成






















-----------------------------------------------