# 李品緯(JasonLee)
# SQL 管理 (要找資料就叫我，記得告訴我要找誰的 user_id)

class UserRepository:
    def __init__(self, db):

        self.db = db # 取得 connect 物件

    def create_user_data(self, items):

        cursor = self.db.cursor()
        cursor.execute("""
        INSERT INTO users (user_id, user_name, email, password, created_at)
        VALUES (?,?,?,?,?) """,(items.user_id,
                                items.user_name,
                                items.email,
                                items.password,
                                items.created_at.isoformat()))
        self.db.commit()

        return items

    # 查詢所有使用者資料
    def get_all_users(self):

        cursor = self.db.cursor()

        cursor.execute("SELECT user_id, user_name, email, password, created_at FROM users")

        return cursor.fetchall()


    def get_user_by_id(self, user_id):

        cursor = self.db.cursor()

        cursor.execute("""
        SELECT user_id, user_name, email, password, created_at FROM users
        WHERE user_id = ? """, (user_id,))

        return cursor.fetchone()

    def update_user_by_id(self, new_name, new_email, new_password, user_id):

        cursor = self.db.cursor()

        cursor.execute("""
        UPDATE users SET user_name = ?, email = ? , password = ?
        WHERE user_id = ? """,(new_name,
                               new_email,
                               new_password,
                               user_id))

        return self.db.commit()

    def delete_user_by_id(self, user_id):

        cursor = self.db.cursor()

        cursor.execute("DELETE FROM users WHERE user_id = ?"
                       ,(user_id,))

        return self.db.commit()

    def get_user_by_email(self, email):

        cursor = self.db.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?",(email,))

        return cursor.fetchone()


