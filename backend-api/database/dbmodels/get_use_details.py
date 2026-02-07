from database.database import SessionLocal
from services.models.models import User

# Get all user details
def userdetails():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return users
    finally:
        db.close()

# Get all admin users
def get_admin():
    db = SessionLocal()
    try:
        admins = db.query(User).filter(User.role_name == 'admin').all()
        return admins
    finally:
        db.close()