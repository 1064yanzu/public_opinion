"""Initialize database with an admin user"""
import sys
sys.path.insert(0, '/home/engine/project')

from backend.app.database import SessionLocal, init_db
from backend.app.models.user import User, UserRole
from backend.app.core.security import get_password_hash

def create_admin():
    """Create admin user if not exists"""
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("Admin user already exists")
            return
        
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("⚠️  Please change the password after first login!")
    except Exception as e:
        print(f"Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
