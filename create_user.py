from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin_user():
    db = SessionLocal()
    try:
        # 删除现有用户
        db.query(User).delete()
        db.commit()
        
        # 创建新用户
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("用户创建成功！")
        print("用户名: admin")
        print("密码: admin123")
    except Exception as e:
        print(f"创建用户失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 