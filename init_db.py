from app.db.init_db import init_db

def init():
    init_db()


if __name__ == "__main__":
    print("创建初始数据库...")
    init()
    print("初始数据库创建完成")