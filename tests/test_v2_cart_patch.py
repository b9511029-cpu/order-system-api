# 李品緯(JasonLee)
import sqlite3
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from API作品.app.cart_api_main import app, DB_PATH


#--------------------------------------------------------------
# SQLite DB clear
#--------------------------------------------------------------
@pytest.fixture(autouse=True)
def db_clear():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cart_items")
    cursor.execute("DELETE FROM carts")

    conn.commit()
    conn.close()

    yield

#-------------------------
# FastAPI Test
#-------------------------
client = TestClient(app)

# SQLite + API test
#--------------------------------------------------------------
# update (Patch) Test
#--------------------------------------------------------------
























