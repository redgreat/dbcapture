from app.database import SessionLocal
from app.models.users import User
from app.core.security import get_password_hash


def create_admin_user():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            return

        # 创建管理员用户
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("管理员用户创建成功")
    except Exception as e:
        print(f"创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
