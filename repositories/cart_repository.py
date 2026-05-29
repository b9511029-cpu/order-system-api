# 李品緯(JasonLee)
from uuid import uuid4

class CartRepository:
    def __init__(self, db):

        self.db = db

    def create_a_new_cart(self, user_id, now_time):
        cart_id = str(uuid4())

        cursor = self.db.cursor()

        cursor.execute(""" INSERT INTO carts (id, user_id, updated_at) 
                        VALUES(?,?,?) """, (cart_id, user_id, now_time))

        self.db.commit()

        return cart_id

    def check_cart_item_quantity(self, cart_id, meal_id):

        cursor = self.db.cursor()

        cursor.execute(""" SELECT quantity FROM cart_items WHERE cart_id = ? 
                           AND menu_item_id = ? """, (cart_id, str(meal_id)))

        return cursor.fetchone()

    def cart_item_accumulation_quantity(self, quantity, cart_id, meal_id):

        cursor = self.db.cursor()

        cursor.execute(""" UPDATE cart_items SET quantity = quantity + ? 
                           WHERE cart_id = ? AND menu_item_id = ? """
                       , (quantity, cart_id, str(meal_id)))

        self.db.commit()

    def add_new_cart_item_to_cart(self, ci_id, orig_cid, req_menu_id, req_quantity, now_time):

        cursor = self.db.cursor()

        cursor.execute(""" INSERT INTO cart_items (id, cart_id, menu_item_id, quantity, added_at)
                        VALUES(?,?,?,?,?) """,
                       (str(ci_id), orig_cid, str(req_menu_id), req_quantity, now_time))

        self.db.commit()

    def add_the_cart_updated_at_time(self, now_time, orig_cid):

        cursor = self.db.cursor()

        cursor.execute("UPDATE carts SET updated_at = ? WHERE id = ?",
                       (now_time, orig_cid))

        self.db.commit()


    def get_the_cart_id_by_user_id(self, user_id):

        cursor = self.db.cursor()

        cursor.execute("SELECT id FROM carts WHERE user_id = ?",(user_id,))

        return cursor.fetchone()

    def get_cart_rows_by_user_id(self, user_id):

        cursor = self.db.cursor()

        cursor.execute("SELECT id, updated_at FROM carts WHERE user_id = ?"
                       , (user_id,))

        return cursor.fetchone()

    def get_now_cart_items_by_cart_id(self, c_id):

        cursor = self.db.cursor()

        cursor.execute("""SELECT menu_item_id, quantity FROM cart_items 
                          WHERE cart_id = ? """, (str(c_id),))

        return cursor.fetchall()

    def delete_cart_items_by_cart_id_and_menu_item_id(self, cart_id, meal_id):

        cursor = self.db.cursor()

        cursor.execute(""" 
        DELETE FROM cart_items WHERE cart_id = ? AND menu_item_id = ? 
        """, (cart_id, str(meal_id))
        )
        self.db.commit()

    def update_cart_item_quantity(self, qty, c_id, m_i_id):

        cursor = self.db.cursor()

        cursor.execute(""" UPDATE cart_items SET quantity = ? 
                           WHERE cart_id = ? AND menu_item_id = ? """
                       , (qty, c_id, str(m_i_id)))

        self.db.commit()

    def get_menu_item_id_and_quantity_by_cid_and_mid(self, cart_id, meal_id):

        cursor = self.db.cursor()

        cursor.execute(""" SELECT menu_item_id, quantity FROM cart_items 
                            WHERE cart_id = ? AND menu_item_id = ? """
                       , (cart_id, str(meal_id))
                       )

        return cursor.fetchall()
