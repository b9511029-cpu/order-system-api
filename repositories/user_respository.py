# 李品緯(JasonLee)
# SQL 管理 (要找資料就叫我，記得告訴我要找誰的 user_id)

print("execute UserRespository.py")
class UserRepository:
    def __init__(self, items, db):

        self.db = db # 取得 connect 物件
        self.items = items


    def add_user(self):

        cursor = self.db.cursor()

        cursor.execute("""
        SELECT user_id, user_name, email, password, created_at FROM users
        WHERE user_id = ? """, (self.items.user_id,))

        return cursor.fetchone()


    def insert_user_data(self):

        cursor = self.db.cursor()
        cursor.execute("""
        INSERT INTO users (user_id, user_name, email, password, created_at)
        VALUES (?,?,?,?,?) """,(self.items.user_id,
                                self.items.user_name,
                                self.items.email,
                                self.items.password,
                                self.items.created_at))
        self.db.commit()

        return self.items



    # 查詢所有使用者資料
    def get_all_users(self):

        cursor = self.db.cursor()

        cursor.execute("SELECT user_id, user_name, email, password, created_at FROM users")

        return cursor.fetchall()


    def get_user_by_id(self, user_id: int):

        cursor = self.db.cursor()

        cursor.execute("""
        SELECT user_id, user_name, email, password, created_at FROM users
        WHERE user_id = ? """, (user_id,))

        return cursor.fetchone()