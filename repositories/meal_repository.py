# 李品緯(JasonLee)

class MealRepository():

    def __init__(self, db):

        self.db = db

    def get_meal_id_by_id(self, m_id):

        cursor = self.db.cursor()

        cursor.execute("SELECT id FROM menus WHERE id = ?", (str(m_id),))

        return cursor.fetchone()

    def create_meal_data(self, m_id, m_name, m_price, m_description, m_image_url):

        cursor = self.db.cursor()

        cursor.execute("""INSERT INTO menus (id, name, price, description, image_url) 
        VALUES (?,?,?,?,?) """,(str(m_id),m_name,m_price,m_description,m_image_url))

        self.db.commit()

    def get_all_meals(self):

        cursor = self.db.cursor()

        cursor.execute("SELECT id, name, price, description, image_url FROM menus")

        return cursor.fetchall()

    def get_meal_by_id(self, meal_id):

        cursor = self.db.cursor()

        cursor.execute("""
        SELECT id, name, price, description, image_url FROM menus 
        WHERE id = ? """,(str(meal_id),))

        return cursor.fetchone()

    def update_meal_all_data(self, name, price, description, image_url, item_id):

        cursor = self.db.cursor()

        cursor.execute("""
        UPDATE menus SET name = ?, price = ?, description = ?, image_url = ?
        WHERE id = ? """,(name, price, description, image_url, str(item_id)))

        self.db.commit()

        # 未測試過 patch API 還未改
    def find_meal_by_id(self, m_id):

        cursor = self.db.cursor()

        cursor.execute("""SELECT * FROM menus WHERE id = ?""",(str(m_id),))

        return cursor.fetchone()

    def update_meal_fields(self, item_id, update_data):

        cursor = self.db.cursor()

        # 動態組 SQL
        set_clause = ", ".join(
            [f"{key} = ?"for key in update_data.keys()]
        )

        # 更新值
        values = list(update_data.values())

        values.append(str(item_id))

        sql = f"UPDATE menus SET {set_clause} WHERE id = ?"

        cursor.execute(sql, values)

        self.db.commit()

    def delete_meal_by_id(self, item_id):

        cursor = self.db.cursor()

        cursor.execute("DELETE FROM menus WHERE id = ?", (str(item_id),))

        self.db.commit()




