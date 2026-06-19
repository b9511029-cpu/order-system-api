# 李品緯(JasonLee)
from uuid import uuid4
from datetime import datetime
from routes.order import OrderStatus


class OrderRepository():
    def __init__(self, db):
        self.db = db

    def create_order(self, user_id: int):
        pass

    def get_orders_by_user(self, user_id: int):
        # 操作 資料庫 SQL
        pass

    def get_order_by_id(self, order_id: str):

        pass

    def cancel_order(self, order_id: str):

        pass

    # 目前先建立個空殼子，暫時不實作