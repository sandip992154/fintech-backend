from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from services.models.models import LoginAttempt, IPBlocklist, User
from services.schemas import schemas

class RateLimiter:
    def __init__(self):
        self.max_attempts = 5  # Max attempts before blocking
        self.attempt_window = timedelta(minutes=15)  # Time window for counting attempts
        self.block_duration = timedelta(hours=1)  # How long to block after max attempts
        self.ip_rate_limit = 30  # Max attempts per IP in attempt_window
    
    async def check_ip_blocked(self, db: Session, ip_address: str) -> Optional[datetime]:
        """Check if an IP is currently blocked"""
        block = db.query(IPBlocklist).filter(
            IPBlocklist.ip_address == ip_address,
            IPBlocklist.blocked_until > datetime.utcnow()
        ).first()
        
        return block.blocked_until if block else None

    async def track_attempt(
        self,
        db: Session,
        request: Request,
        identifier: str,
        success: bool,
        attempt_type: str
    ) -> None:
        """Record a login attempt"""
        # Create attempt record
        attempt = LoginAttempt(
            ip_address=request.client.host,
            identifier=identifier,
            success=success,
            attempt_type=attempt_type,
            user_agent=request.headers.get("user-agent"),
            location=request.headers.get("x-real-ip")  # If behind proxy
        )
        db.add(attempt)
        
        if not success:
            # Check for repeated failures
            recent_failures = db.query(LoginAttempt).filter(
                LoginAttempt.identifier == identifier,
                LoginAttempt.success == False,
                LoginAttempt.attempt_time > datetime.utcnow() - self.attempt_window
            ).count()
            
            if recent_failures >= self.max_attempts:
                # Lock user account if it exists
                user = db.query(User).filter(
                    (User.username == identifier) |
                    (User.email == identifier) |
                    (User.phone == identifier)
                ).first()
                
                if user:
                    user.status = schemas.UserStatus.LOCKED
                
                # Block IP address
                block = IPBlocklist(
                    ip_address=request.client.host,
                    blocked_until=datetime.utcnow() + self.block_duration,
                    reason=f"Too many failed attempts for identifier: {identifier}"
                )
                db.add(block)
        
        db.commit()

    async def check_rate_limit(
        self,
        db: Session,
        request: Request,
        identifier: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if the request should be rate limited
        Returns (is_allowed, error_message)
        """
        # Check IP blocklist
        block_until = await self.check_ip_blocked(db, request.client.host)
        if block_until:
            return False, f"IP address blocked until {block_until}"
        
        # Check IP rate limit
        ip_attempts = db.query(LoginAttempt).filter(
            LoginAttempt.ip_address == request.client.host,
            LoginAttempt.attempt_time > datetime.utcnow() - self.attempt_window
        ).count()
        
        if ip_attempts >= self.ip_rate_limit:
            # Add IP to blocklist
            block = IPBlocklist(
                ip_address=request.client.host,
                blocked_until=datetime.utcnow() + self.block_duration,
                reason="IP rate limit exceeded"
            )
            db.add(block)
            db.commit()
            return False, "Too many attempts from this IP address"
        
        # Check identifier-specific attempts
        identifier_attempts = db.query(LoginAttempt).filter(
            LoginAttempt.identifier == identifier,
            LoginAttempt.success == False,
            LoginAttempt.attempt_time > datetime.utcnow() - self.attempt_window
        ).count()
        
        if identifier_attempts >= self.max_attempts:
            return False, f"Too many failed attempts for this {identifier}"
        
        return True, None

# Global rate limiter instance
rate_limiter = RateLimiter()