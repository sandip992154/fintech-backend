from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.database import get_db
from services.models.superadmin_model import SuperAdmin
from utils.security import (
    verify_password,
    create_access_token,
    verify_token
)
from datetime import timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate_superadmin(db: Session, username: str, password: str):
    superadmin = db.query(SuperAdmin).filter(SuperAdmin.username == username).first()
    if not superadmin or not verify_password(password, superadmin.password):
        return None
    return superadmin

def create_superadmin_token(superadmin: SuperAdmin):
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": superadmin.username, "role": "superadmin"},
        expires_delta=access_token_expires
    )
    return access_token

async def get_current_superadmin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        if payload.get("role") != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized for superadmin access"
            )
    except:
        raise credentials_exception
        
    superadmin = db.query(SuperAdmin).filter(SuperAdmin.username == username).first()
    if superadmin is None:
        raise credentials_exception
    return superadmin