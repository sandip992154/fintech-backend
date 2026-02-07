"""
Member Management Business Logic Service
Handles all business logic for member operations
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, desc
from fastapi import HTTPException, status
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

from services.models.models import User, Role
from services.schemas.member_schema import (
    MemberCreateRequest, MemberOut, MemberUpdateRequest,
    MemberStatusUpdateRequest
)
from services.utils.member_utils import (
    normalize_phone, can_manage_role, get_creatable_roles,
    create_member_out, determine_parent_id, build_member_query,
    validate_member_data, log_member_action, log_member_error
)
from services.auth.auth import get_password_hash
from utils.email_utils import send_account_email
from config.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class MemberService:
    """Service class for member management business logic"""
    
    def __init__(self):
        pass
    
    # ======================== Permission Validation ========================
    
    def validate_member_permissions(self, current_user: User, target_role: str, action: str = "create"):
        """Validate if current user has permission to perform action on target role"""
        current_role = current_user.role.name
        
        if action == "create":
            creatable_roles = get_creatable_roles(current_role)
            if target_role not in creatable_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to create {target_role} members. You can only create: {', '.join(creatable_roles)}"
                )
        elif action in ["update", "delete", "manage"]:
            if not can_manage_role(current_role, target_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to {action} {target_role} members"
                )
    
    # ======================== Member Creation ========================
    
    def create_member(self, member_data: MemberCreateRequest, current_user: User, db: Session) -> Tuple[MemberOut, str]:
        """
        Create a new member with comprehensive validation and business logic
        Returns: (member_out, email_error_if_any)
        """
        try:
            # Validate permissions
            self.validate_member_permissions(current_user, member_data.role_name, "create")
            
            # Validate member data
            validation = validate_member_data(member_data)
            if not validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation errors: {', '.join(validation['errors'])}"
                )
            
            # Check if email or phone already exists
            normalized_phone = normalize_phone(member_data.phone)
            
            existing_by_email = db.query(User).filter(User.email == member_data.email).first()
            if existing_by_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with email '{member_data.email}' already exists"
                )
            
            existing_by_phone = db.query(User).filter(User.phone == normalized_phone).first()
            if existing_by_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with phone '{member_data.phone}' already exists"
                )
            
            # Get role object
            role_obj = db.query(Role).filter(Role.name == member_data.role_name).first()
            if not role_obj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role '{member_data.role_name}' not found"
                )
            
            # Generate user code
            user_code = self._generate_user_code(member_data.role_name, db)
            
            # Use user_code as default password if not provided
            raw_password = member_data.password if hasattr(member_data, 'password') and member_data.password else user_code
            
            # Determine parent ID
            parent_id = determine_parent_id(member_data, current_user, db)
            
            # Validate parent if provided
            if parent_id:
                parent_user = db.query(User).filter(User.id == parent_id).first()
                if not parent_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Parent user not found"
                    )
                
                # Validate parent role hierarchy
                parent_role = parent_user.role.name
                if not can_manage_role(parent_role, member_data.role_name):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{parent_role} cannot be parent of {member_data.role_name}"
                    )
            
            # Create new user
            new_member = User(
                user_code=user_code,
                username=user_code,
                email=member_data.email,
                phone=normalize_phone(member_data.phone),
                mobile=normalize_phone(getattr(member_data, 'mobile', member_data.phone)),
                full_name=member_data.full_name,
                hashed_password=get_password_hash(raw_password),
                role_id=role_obj.id,
                parent_id=parent_id,
                
                # Address fields
                address=getattr(member_data, 'address', None),
                pin_code=getattr(member_data, 'pin_code', None),
                
                # Business fields
                shop_name=getattr(member_data, 'shop_name', None),
                company_name=getattr(member_data, 'company_name', None),
                scheme=getattr(member_data, 'scheme', None),
                
                # KYC fields
                pan_card_number=getattr(member_data, 'pan_card_number', None),
                company_pan_card=getattr(member_data, 'company_pan_card', None),
                aadhaar_card_number=getattr(member_data, 'aadhaar_card_number', None),
                
                is_active=True
            )
            
            try:
                db.add(new_member)
                db.commit()
                db.refresh(new_member)
            except IntegrityError as e:
                db.rollback()
                logger.error(f"Database integrity error during member creation: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Member creation failed due to data integrity constraints"
                )
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Database error during member creation: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database error occurred during member creation"
                )
            
            # Send welcome email (don't fail member creation if email fails)
            email_error = None
            try:
                email_error = self._send_welcome_email(new_member, raw_password)
            except Exception as e:
                logger.warning(f"Failed to send welcome email to {new_member.email}: {str(e)}")
                email_error = "Failed to send welcome email"
            
            # Log successful creation
            try:
                log_member_action("created", new_member.user_code, current_user.user_code,
                                f"Role: {member_data.role_name}")
            except Exception as e:
                logger.warning(f"Failed to log member creation: {str(e)}")
            
            return create_member_out(new_member), email_error
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Ensure rollback for any other exceptions
            try:
                db.rollback()
            except Exception:
                pass
            
            # Log the error
            try:
                log_member_error("creation", "unknown", current_user.user_code, str(e))
            except Exception:
                pass
            
            logger.error(f"Unexpected error creating member: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create member"
            )
    
    # ======================== Member Listing ========================
    
    def list_members(self, current_user: User, db: Session, page: int = 1, limit: int = 10,
                    role_filter: Optional[str] = None, is_active: Optional[bool] = None,
                    search: Optional[str] = None) -> Tuple[List[MemberOut], int]:
        """
        List members with pagination and filters
        Returns: (member_list, total_count)
        """
        try:
            # Build query
            query = build_member_query(db, current_user, role_filter, is_active, search)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            members = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
            
            # Convert to response format
            member_list = [create_member_out(member) for member in members]
            
            return member_list, total
            
        except Exception as e:
            logger.error(f"Error listing members: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve members"
            )
    
    # ======================== Member Details ========================
    
    def get_member_details(self, member_id: int, current_user: User, db: Session) -> MemberOut:
        """Get details of a specific member"""
        try:
            # Get member
            member = db.query(User).filter(User.id == member_id).first()
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found"
                )
            
            # Check permissions
            self.validate_member_permissions(current_user, member.role.name, "manage")
            
            return create_member_out(member)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting member details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve member details"
            )
    
    # ======================== Member Update ========================
    
    def update_member(self, member_id: int, update_data: MemberUpdateRequest,
                     current_user: User, db: Session) -> MemberOut:
        """Update member information"""
        try:
            # Get member
            member = db.query(User).filter(User.id == member_id).first()
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found"
                )
            
            # Check permissions
            self.validate_member_permissions(current_user, member.role.name, "update")
            
            # Validate update data
            validation = validate_member_data(update_data)
            if not validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation errors: {', '.join(validation['errors'])}"
                )
            
            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Check for duplicate email/phone if being updated
            if 'email' in update_dict and update_dict['email'] != member.email:
                existing_email = db.query(User).filter(
                    User.email == update_dict['email'],
                    User.id != member_id
                ).first()
                if existing_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Email '{update_dict['email']}' is already in use"
                    )
            
            if 'phone' in update_dict:
                normalized_phone = normalize_phone(update_dict['phone'])
                if normalized_phone != member.phone:
                    existing_phone = db.query(User).filter(
                        User.phone == normalized_phone,
                        User.id != member_id
                    ).first()
                    if existing_phone:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Phone '{update_dict['phone']}' is already in use"
                        )
                update_dict['phone'] = normalized_phone
            
            if 'mobile' in update_dict:
                update_dict['mobile'] = normalize_phone(update_dict['mobile'])
            
            for field, value in update_dict.items():
                if hasattr(member, field):
                    setattr(member, field, value)
            
            member.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(member)
            
            # Log successful update
            log_member_action("updated", member.user_code, current_user.user_code)
            
            return create_member_out(member)
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            log_member_error("update", str(member_id), current_user.user_code, str(e))
            logger.error(f"Error updating member: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update member"
            )
    
    # ======================== Member Status Update ========================
    
    def update_member_status(self, member_id: int, status_data: MemberStatusUpdateRequest,
                           current_user: User, db: Session) -> Dict[str, Any]:
        """Update member active status"""
        try:
            # Get member
            member = db.query(User).filter(User.id == member_id).first()
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found"
                )
            
            # Check permissions
            self.validate_member_permissions(current_user, member.role.name, "update")
            
            # Update status
            old_status = member.is_active
            member.is_active = status_data.is_active
            member.updated_at = datetime.utcnow()
            
            db.commit()
            
            action = "activated" if status_data.is_active else "deactivated"
            log_member_action(action, member.user_code, current_user.user_code)
            
            return {
                "message": f"Member {action} successfully",
                "member_id": member_id,
                "new_status": status_data.is_active,
                "old_status": old_status
            }
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            log_member_error("status_update", str(member_id), current_user.user_code, str(e))
            logger.error(f"Error updating member status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update member status"
            )
    
    # ======================== Member Deletion ========================
    
    def delete_member(self, member_id: int, current_user: User, db: Session) -> Dict[str, Any]:
        """Delete a member (soft delete by deactivating)"""
        try:
            # Get member
            member = db.query(User).filter(User.id == member_id).first()
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found"
                )
            
            # Check if member is already deleted
            if not member.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Member is already deactivated"
                )
            
            # Check permissions
            self.validate_member_permissions(current_user, member.role.name, "delete")
            
            # Check if member has active children
            active_children = db.query(User).filter(
                User.parent_id == member_id,
                User.is_active == True
            ).count()
            
            if active_children > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete member with {active_children} active children. Please deactivate children first."
                )
            
            # Prevent self-deletion
            if member_id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You cannot delete your own account"
                )
            
            # Soft delete (deactivate)
            try:
                member.is_active = False
                member.updated_at = datetime.utcnow()
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Database error during member deletion: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database error occurred during member deletion"
                )
            
            # Log the action
            try:
                log_member_action("deleted", member.user_code, current_user.user_code)
            except Exception as e:
                logger.warning(f"Failed to log member deletion: {str(e)}")
            
            return {
                "message": "Member deleted successfully",
                "member_id": member_id,
                "user_code": member.user_code
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Ensure rollback for any other exceptions
            try:
                db.rollback()
            except Exception:
                pass
            
            # Log the error
            try:
                log_member_error("deletion", str(member_id), current_user.user_code, str(e))
            except Exception:
                pass
            
            logger.error(f"Unexpected error deleting member {member_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete member"
            )
    
    # ======================== Reference Data Methods ========================
    
    def get_schemes(self, current_user: User, db: Session):
        """Get available schemes for member creation"""
        from services.schemas.member_admin_schema import SchemeListResponse, SchemeOption
        
        try:
            # For now, return mock data since we don't have a schemes table
            # In production, this would query from a schemes table
            schemes = [
                SchemeOption(
                    id="scheme_001",
                    name="Basic Scheme",
                    description="Basic member scheme with standard features",
                    commission_rate=1.0,
                    is_active=True
                ),
                SchemeOption(
                    id="scheme_002", 
                    name="Premium Scheme",
                    description="Premium member scheme with enhanced features",
                    commission_rate=1.5,
                    is_active=True
                ),
                SchemeOption(
                    id="scheme_003",
                    name="Enterprise Scheme", 
                    description="Enterprise member scheme with advanced features",
                    commission_rate=2.0,
                    is_active=True
                )
            ]
            
            return SchemeListResponse(
                schemes=schemes,
                total=len(schemes)
            )
            
        except Exception as e:
            logger.error(f"Error getting schemes for user {current_user.user_code}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch schemes"
            )
    
    def get_locations(self):
        """Get available locations (states and cities)"""
        from services.schemas.member_admin_schema import LocationOptionsResponse, StateOption, CityOption
        
        try:
            # Mock data for Indian states and major cities
            # In production, this would come from a locations database
            states = [
                StateOption(id="MH", name="Maharashtra", code="MH"),
                StateOption(id="KA", name="Karnataka", code="KA"), 
                StateOption(id="TN", name="Tamil Nadu", code="TN"),
                StateOption(id="AP", name="Andhra Pradesh", code="AP"),
                StateOption(id="TS", name="Telangana", code="TS"),
                StateOption(id="GJ", name="Gujarat", code="GJ"),
                StateOption(id="RJ", name="Rajasthan", code="RJ"),
                StateOption(id="UP", name="Uttar Pradesh", code="UP"),
                StateOption(id="WB", name="West Bengal", code="WB"),
                StateOption(id="DL", name="Delhi", code="DL")
            ]
            
            cities = [
                # Maharashtra
                CityOption(id="MH001", name="Mumbai", state_id="MH"),
                CityOption(id="MH002", name="Pune", state_id="MH"),
                CityOption(id="MH003", name="Nagpur", state_id="MH"),
                CityOption(id="MH004", name="Nashik", state_id="MH"),
                # Karnataka
                CityOption(id="KA001", name="Bangalore", state_id="KA"),
                CityOption(id="KA002", name="Mysore", state_id="KA"),
                CityOption(id="KA003", name="Hubli", state_id="KA"),
                # Tamil Nadu
                CityOption(id="TN001", name="Chennai", state_id="TN"),
                CityOption(id="TN002", name="Coimbatore", state_id="TN"),
                CityOption(id="TN003", name="Madurai", state_id="TN"),
                # Andhra Pradesh
                CityOption(id="AP001", name="Visakhapatnam", state_id="AP"),
                CityOption(id="AP002", name="Vijayawada", state_id="AP"),
                # Telangana
                CityOption(id="TS001", name="Hyderabad", state_id="TS"),
                CityOption(id="TS002", name="Warangal", state_id="TS"),
                # Gujarat
                CityOption(id="GJ001", name="Ahmedabad", state_id="GJ"),
                CityOption(id="GJ002", name="Surat", state_id="GJ"),
                # Delhi
                CityOption(id="DL001", name="New Delhi", state_id="DL"),
                CityOption(id="DL002", name="Delhi", state_id="DL")
            ]
            
            return LocationOptionsResponse(
                states=states,
                cities=cities
            )
            
        except Exception as e:
            logger.error(f"Error getting locations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch locations"
            )
    
    def get_dashboard_stats(self, current_user: User, db: Session, 
                           include_financial: bool = False,
                           include_system_wide: bool = False):
        """Get dashboard statistics for member management"""
        from services.schemas.member_admin_schema import MemberDashboardStats
        from datetime import datetime, timedelta
        
        try:
            # Get total members count
            total_members = db.query(func.count(User.id)).scalar() or 0
            
            # Get active and inactive members
            active_members = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
            inactive_members = total_members - active_members
            
            # Get role distribution (only active users)
            role_distribution = {}
            roles = db.query(Role).all()
            
            for role in roles:
                count = db.query(func.count(User.id)).filter(
                    User.role_id == role.id,
                    User.is_active == True
                ).scalar() or 0
                if count > 0:
                    role_distribution[role.name] = count
            
            # Get recent registrations (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_registrations = db.query(func.count(User.id)).filter(
                User.created_at >= seven_days_ago,
                User.is_active == True
            ).scalar() or 0
            
            # Get recent activations (last 7 days) - assuming updated_at tracks status changes
            recent_activations = db.query(func.count(User.id)).filter(
                User.updated_at >= seven_days_ago,
                User.is_active == True
            ).scalar() or 0
            
            # KYC stats - assuming kyc_status field exists on User model
            pending_kyc = db.query(func.count(User.id)).filter(
                User.is_active == True
            ).scalar() or 0  # Placeholder - adjust based on actual KYC field
            
            completed_kyc = db.query(func.count(User.id)).filter(
                User.is_active == True
            ).scalar() or 0  # Placeholder - adjust based on actual KYC field
            
            # Create and return dashboard stats
            dashboard_stats = MemberDashboardStats(
                total_members=total_members,
                active_members=active_members,
                inactive_members=inactive_members,
                pending_kyc=pending_kyc,
                completed_kyc=completed_kyc,
                role_distribution=role_distribution,
                recent_registrations=recent_registrations,
                recent_activations=recent_activations,
                total_wallet_balance=0.0  # Can be calculated if wallet data exists
            )
            
            logger.info(f"Dashboard stats retrieved: {total_members} total members, {active_members} active")
            return dashboard_stats
            
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {str(e)}")
            # Return default stats instead of raising exception
            return MemberDashboardStats(
                total_members=0,
                active_members=0,
                inactive_members=0,
                pending_kyc=0,
                completed_kyc=0,
                role_distribution={},
                recent_registrations=0,
                recent_activations=0,
                total_wallet_balance=0.0
            )

    def get_parent_options(self, current_user: User, db: Session, 
                          role_filter: Optional[str] = None,
                          search_query: Optional[str] = None,
                          manageable_roles: List[str] = None):
        """Get available parent options for member creation based on hierarchy"""
        from services.schemas.member_schema import ParentSelectionResponse, ParentSelectionOption
        from sqlalchemy import or_
        
        try:
            # Build query for potential parents
            query = db.query(User).join(Role)
            
            # SuperAdmin can see all users as potential parents
            if current_user.role.name == "super_admin":
                query = query.filter(User.is_active == True)
            else:
                # Other users can only see users in their hierarchy
                query = query.filter(
                    or_(
                        User.id == current_user.id,  # Self as parent
                        User.parent_id == current_user.id,  # Direct children
                        User.id == current_user.parent_id  # Own parent
                    )
                ).filter(User.is_active == True)
            
            # Apply role filter if provided
            if role_filter:
                query = query.filter(Role.name == role_filter)
            
            # Apply search filter if provided
            if search_query:
                search_term = f"%{search_query}%"
                query = query.filter(
                    or_(
                        User.full_name.ilike(search_term),
                        User.email.ilike(search_term),
                        User.user_code.ilike(search_term)
                    )
                )
            
            # Execute query
            potential_parents = query.order_by(User.full_name).limit(50).all()
            
            # Convert to response format
            parent_options = [
                ParentSelectionOption(
                    id=parent.id,
                    name=parent.full_name,
                    user_code=parent.user_code,
                    role_name=parent.role.name,
                    email=parent.email,
                    is_active=parent.is_active
                )
                for parent in potential_parents
            ]
            
            return ParentSelectionResponse(
                success=True,
                parents=parent_options,
                message=f"Found {len(parent_options)} potential parents"
            )
            
        except Exception as e:
            logger.error(f"Error fetching parent options for user {current_user.user_code}: {str(e)}")
            return ParentSelectionResponse(
                success=False,
                parents=[],
                message="Failed to fetch parent options"
            )

    # ======================== Private Helper Methods ========================

    def _generate_user_code(self, role: str, db: Session) -> str:
        """Generate unique user code for the role"""
        from utils.user_code_generator import generate_unique_user_code
        return generate_unique_user_code(role, db)
    
    def _send_welcome_email(self, member: User, password: str) -> Optional[str]:
        """Send welcome email to new member"""
        try:
            login_link = f"{getattr(settings, 'FRONTEND_URL', 'https://app.bandarupay.com')}/login"
            
            send_account_email(
                smtp_server=settings.SMTP_SERVER,
                smtp_port=settings.SMTP_PORT,
                smtp_user=settings.SMTP_USER,
                smtp_password=settings.SMTP_PASSWORD,
                to_email=member.email,
                user_id=member.user_code,
                password=password,
                signup_link=login_link,
                role=member.role.name
            )
            
            logger.info(f"Welcome email sent successfully to {member.email}")
            return None
            
        except Exception as e:
            error_msg = f"Failed to send welcome email to {member.email}: {str(e)}"
            logger.warning(error_msg)
            return error_msg

# Create singleton instance
member_service = MemberService()