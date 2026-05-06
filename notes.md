#------------------------------
# 購物車 開發筆記/Debug 紀錄
#------------------------------

---
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
Q3: 


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








---













#-----------------------------
# 使用者 開發筆記/Debug 紀錄
#-----------------------------

---



#-----------------------------
# 餐點 開發筆記/Debug 紀錄
#-----------------------------

---