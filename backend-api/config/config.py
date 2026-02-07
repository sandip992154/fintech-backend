from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Bandaru Pay API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    EMAIL_SENDER: str = "no-reply@bandarupay.com"
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bandaru_pay_prod_secret_key_2025_09_21")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 28800  # 20 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Redis Settings for Session Management
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_SSL: bool = os.getenv("REDIS_SSL", "False").lower() == "true"
    
    # Rate Limiting
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_MAX_REQUESTS: int = 100
    
    # Session Settings
    MAX_SESSIONS_PER_USER: int = 5
    SESSION_IDLE_TIMEOUT: int = 480  # 8 hours
    
    # OTP Settings
    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 5
    MAX_OTP_ATTEMPTS: int = 3
    OTP_COOLDOWN_MINUTES: int = 15
    
    # SMTP Settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "your-email@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "your-app-specific-password")
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:root@localhost/bandaru_pay")
    
    # CORS Settings
    CORS_ORIGINS: list = [
        "http://localhost:5173",  # Superadmin
        "http://localhost:5174",  # Admin
        "http://localhost:5175",  # Whitelabel
        "http://localhost:5176",  # MDS
        "http://localhost:5177",  # Distributor
        "http://localhost:5178",  # Retailer
        "http://localhost:5179",  # Customer
        "http://localhost:5180",  # Website
    ]
    
    # Email Settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "no-reply@bandarupay.com")
    
    # Superadmin Settings
    SUPERADMIN_USERNAME: str = os.getenv("SUPERADMIN_USERNAME", "superadmin")
    SUPERADMIN_EMAIL: str = os.getenv("SUPERADMIN_EMAIL", "superadmin@bandarupay.com")
    SUPERADMIN_PHONE: str = os.getenv("SUPERADMIN_PHONE", "+919999999999")
    SUPERADMIN_PASSWORD: str = os.getenv("SUPERADMIN_PASSWORD", "SuperAdmin@123")
    SUPERADMIN_NAME: str = os.getenv("SUPERADMIN_NAME", "Super Admin")
    SUPERADMIN_USER_CODE: str = os.getenv("SUPERADMIN_USER_CODE", "BANDSU00001")
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow"  # Allow extra fields
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Singleton instance
settings = get_settings()