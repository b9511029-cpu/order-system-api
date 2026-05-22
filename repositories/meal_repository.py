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

