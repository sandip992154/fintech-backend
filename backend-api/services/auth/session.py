from datetime import datetime, timedelta
import uuid
from typing import Optional, List, Dict
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from services.models.models import User, UserSession, TrustedDevice
from services.schemas import schemas

class SessionManager:
    def __init__(self):
        self.max_sessions = 5  # Maximum concurrent sessions per user
        self.session_lifetime = timedelta(days=7)  # How long a session can live
        self.trusted_device_lifetime = timedelta(days=30)  # How long to trust a device
        self.inactive_timeout = timedelta(hours=24)  # How long before a session is considered inactive

    def _generate_device_id(self, request: Request) -> str:
        """Generate a unique device identifier based on request headers"""
        user_agent = request.headers.get("user-agent", "")
        ip = request.client.host
        # Additional headers that might help identify the device
        platform = request.headers.get("sec-ch-ua-platform", "")
        mobile = request.headers.get("sec-ch-ua-mobile", "")
        
        # Combine these factors to create a unique but consistent device ID
        device_factors = f"{user_agent}|{ip}|{platform}|{mobile}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, device_factors))

    def _get_device_info(self, request: Request) -> Dict[str, str]:
        """Extract device information from the request"""
        user_agent = request.headers.get("user-agent", "")
        
        # Basic device type detection
        device_type = "desktop"
        if "mobile" in user_agent.lower():
            device_type = "mobile"
        elif "tablet" in user_agent.lower():
            device_type = "tablet"
        
        return {
            "device_id": self._generate_device_id(request),
            "device_type": device_type,
            "device_name": user_agent[:255],  # Truncate to fit db field
            "ip_address": request.client.host,
            "location": request.headers.get("x-real-ip", None),  # If behind proxy
            "user_agent": user_agent[:512]  # Truncate to fit db field
        }

    async def create_session(
        self,
        db: Session,
        user: User,
        request: Request,
        remember_device: bool = False
    ) -> UserSession:
        """Create a new session for a user"""
        # Clean up expired sessions first
        self.cleanup_expired_sessions(db, user.id)
        
        # Check if maximum session limit is reached
        active_sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user.id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).count()
        
        if active_sessions >= self.max_sessions:
            # Revoke oldest session
            oldest_session = db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user.id,
                    UserSession.is_active == True
                )
            ).order_by(UserSession.last_active).first()
            
            if oldest_session:
                oldest_session.is_active = False
                oldest_session.revoked = True
                oldest_session.revoked_reason = "Max sessions reached"
        
        # Get device information
        device_info = self._get_device_info(request)
        
        # Create new session
        session = UserSession(
            session_id=str(uuid.uuid4()),
            user_id=user.id,
            expires_at=datetime.utcnow() + self.session_lifetime,
            **device_info
        )
        db.add(session)
        
        # Handle trusted device
        if remember_device:
            trusted_device = TrustedDevice(
                user_id=user.id,
                device_id=device_info["device_id"],
                device_name=device_info["device_name"],
                trust_expires=datetime.utcnow() + self.trusted_device_lifetime
            )
            db.add(trusted_device)
        
        db.commit()
        db.refresh(session)
        return session

    def validate_session(
        self,
        db: Session,
        session_id: str,
        request: Request
    ) -> Optional[UserSession]:
        """Validate and update a session"""
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if not session:
            return None
            
        if not session.is_active or session.revoked:
            return None
            
        if session.expires_at < datetime.utcnow():
            session.is_active = False
            db.commit()
            return None
            
        # Check if the session is inactive
        if datetime.utcnow() - session.last_active > self.inactive_timeout:
            session.is_active = False
            session.revoked = True
            session.revoked_reason = "Session inactive"
            db.commit()
            return None
        
        # Update last active time
        session.last_active = datetime.utcnow()
        db.commit()
        
        return session

    def revoke_session(
        self,
        db: Session,
        session_id: str,
        reason: str = "User logged out"
    ) -> None:
        """Revoke a specific session"""
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session:
            session.is_active = False
            session.revoked = True
            session.revoked_reason = reason
            db.commit()

    def revoke_all_user_sessions(
        self,
        db: Session,
        user_id: int,
        except_session_id: Optional[str] = None,
        reason: str = "User logged out all devices"
    ) -> None:
        """Revoke all sessions for a user, optionally keeping one active"""
        query = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        )
        
        if except_session_id:
            query = query.filter(UserSession.session_id != except_session_id)
        
        sessions = query.all()
        for session in sessions:
            session.is_active = False
            session.revoked = True
            session.revoked_reason = reason
        
        db.commit()

    def cleanup_expired_sessions(self, db: Session, user_id: Optional[int] = None) -> None:
        """Clean up expired sessions and trusted devices"""
        # Build base query for expired sessions
        query = db.query(UserSession).filter(
            and_(
                UserSession.expires_at < datetime.utcnow(),
                UserSession.is_active == True
            )
        )
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        # Update expired sessions
        expired_sessions = query.all()
        for session in expired_sessions:
            session.is_active = False
            session.revoked = True
            session.revoked_reason = "Session expired"
        
        # Clean up expired trusted devices
        trusted_query = db.query(TrustedDevice).filter(
            and_(
                TrustedDevice.trust_expires < datetime.utcnow(),
                TrustedDevice.is_active == True
            )
        )
        
        if user_id:
            trusted_query = trusted_query.filter(TrustedDevice.user_id == user_id)
        
        trusted_query.update({"is_active": False})
        
        db.commit()

    def get_active_sessions(self, db: Session, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user"""
        return db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).all()

    def is_trusted_device(
        self,
        db: Session,
        user_id: int,
        device_id: str
    ) -> bool:
        """Check if a device is trusted for a user"""
        device = db.query(TrustedDevice).filter(
            and_(
                TrustedDevice.user_id == user_id,
                TrustedDevice.device_id == device_id,
                TrustedDevice.is_active == True,
                TrustedDevice.trust_expires > datetime.utcnow()
            )
        ).first()
        
        return bool(device)

# Global session manager instance
session_manager = SessionManager()