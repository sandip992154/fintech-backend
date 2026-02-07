from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database import Base
from services.models.models import OTP
from config.config import settings

def cleanup_expired_otps():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Delete expired OTPs that are older than 24 hours
        db.query(OTP).filter(
            OTP.expires_at < datetime.utcnow(),
            OTP.created_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        print("Successfully cleaned up expired OTPs")
        
    except Exception as e:
        print(f"Error cleaning up OTPs: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_expired_otps()