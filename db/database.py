# 李品緯(JasonLee)
# 完成 DB schema 建立與測式後 , 在測試 cart API flow 前 , 需先將連線部分整合 app.db
# DB.py : 提供所有 API 統一連線的管理檔案
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent # 找到這個檔案的根目錄
DB_PATH = BASE_DIR /"db"/"app.db" # 將根目錄的路徑+資料庫的路徑 = 資料庫完整路徑(提供給資料庫連線使用)
DB_PATH.parent.mkdir(parents=True, exist_ok=True) # 確保資料夾存在，如果不存在就幫你建立(自動補齊環境差異)



def get_db_connection():
    """docstring: 該檔案變成 單一職責 建立一個 all API 共用的連線規則
       降低耦合、API連線問題重複性(API 變乾淨),觀念就是 職責分離

    Function 代表 Unified(統一) connect to app.db 模組
    Set foreign_key: ON status , 用途:讓 DB all Table 透過 DB 關係設計 連結
    Set 格式: conn 回傳資料(tuple)時，轉換成 Python 要的 sqlite3.Row 格式 (row['name'])

    :return: conn: 代表已轉換格式的 欄位資料
    """
    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA foreign_keys=ON")

    conn.row_factory = sqlite3.Row

    return conn



