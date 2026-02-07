"""
Business Logic Services for Scheme and Commission Management with Role-Based Access Control
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from decimal import Decimal
import csv
import io
from datetime import datetime

from services.models.scheme_models import (
    Scheme, ServiceOperator, Commission, CommissionSlab,
    ServiceTypeEnum, CommissionTypeEnum
)
from services.models.models import User, Role
from services.auth.token_service import TokenService
from services.schemas.scheme_schemas import (
    SchemeCreate, SchemeUpdate, ServiceOperatorCreate, ServiceOperatorUpdate,
    CommissionCreate, CommissionUpdate, BulkCommissionCreate, CommissionExportData,
    CommissionEntry, AEPSCommissionEntry, CommissionSlabCreate
)
from services.utils.role_hierarchy import RoleHierarchy


class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self, db: Session, token_service: Optional[TokenService] = None):
        self.db = db
        self.token_service = token_service
    
    def extract_user_from_token(self, token: str) -> Tuple[int, str]:
        """Extract user_id and role from JWT token"""
        if not self.token_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token service not available"
            )
        
        try:
            payload = self.token_service.verify_token(token, "access")
            user_id = int(payload.get("sub"))
            user_role = payload.get("role", "customer")
            
            return user_id, user_role
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    def get_subordinate_users(self, user_id: int, current_user_role: str) -> List[int]:
        """Get all users below the specified user in role hierarchy"""
        # Get the role of the specified user
        target_user = self.db.query(User).filter(User.id == user_id).first()
        if not target_user:
            return []
        
        target_role = getattr(target_user, 'role', 'customer')
        manageable_roles = RoleHierarchy.get_manageable_roles(target_role)
        
        # Get all users with manageable roles
        subordinate_users = self.db.query(User.id).filter(
            User.role.in_(manageable_roles)
        ).all()
        
        return [user.id for user in subordinate_users]
    
    def apply_user_access_filter(self, query, model_class, current_user_id: int, current_user_role: str, filter_user_id: Optional[int] = None):
        """Apply user access filtering based on ownership and hierarchy"""
        role_level = RoleHierarchy.get_role_level(current_user_role)
        
        # Non-admin users can only see their own records
        if role_level > 1:  # Not super_admin or admin
            if hasattr(model_class, 'owner_id'):
                query = query.filter(
                    or_(
                        model_class.owner_id == current_user_id,
                        model_class.created_by == current_user_id
                    )
                )
            else:
                query = query.filter(model_class.created_by == current_user_id)
        
        # Filter by specific user and their hierarchy
        if filter_user_id is not None:
            if role_level <= 1:  # super_admin or admin
                subordinate_users = self.get_subordinate_users(filter_user_id, current_user_role)
                subordinate_users.append(filter_user_id)
                
                if hasattr(model_class, 'owner_id'):
                    query = query.filter(
                        or_(
                            model_class.owner_id.in_(subordinate_users),
                            model_class.created_by.in_(subordinate_users)
                        )
                    )
                else:
                    query = query.filter(model_class.created_by.in_(subordinate_users))
            else:
                # Non-admin users can only filter by their own records
                if filter_user_id == current_user_id:
                    if hasattr(model_class, 'owner_id'):
                        query = query.filter(
                            or_(
                                model_class.owner_id == current_user_id,
                                model_class.created_by == current_user_id
                            )
                        )
                    else:
                        query = query.filter(model_class.created_by == current_user_id)
                else:
                    # Return empty query for unauthorized access
                    query = query.filter(False)
        
        return query


class SchemeService(BaseService):
    """Service class for scheme management operations"""
    
    def _get_user_code_by_id(self, user_id: int) -> str:
        """Get user_code by user_id"""
        from services.models.models import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and hasattr(user, 'user_code'):
            return user.user_code
        return f"USER{user_id}"  # Fallback

    def create_scheme(
        self, 
        scheme_data: SchemeCreate, 
        created_by: Optional[int] = None, 
        creator_role: Optional[str] = None,
        owner_id: Optional[int] = None,
        token: Optional[str] = None
    ) -> Scheme:
        """Create a new scheme with user-based ownership"""
        
        # Extract user info from token if not provided
        if not created_by or not creator_role:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required: provide token or user credentials"
                )
            created_by, creator_role = self.extract_user_from_token(token)
        
        # Use created_by as owner_id if owner_id not specified
        if not owner_id:
            owner_id = created_by
        
        # Check if user role can create schemes
        if not RoleHierarchy.can_create_scheme(creator_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{creator_role}' is not authorized to create schemes"
            )
            
        # Check if scheme with same name already exists
        existing = self.db.query(Scheme).filter(
            Scheme.name == scheme_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Scheme with name '{scheme_data.name}' already exists"
            )
        
        # Create new scheme with user ownership
        try:
            db_scheme = Scheme(
                name=scheme_data.name,
                description=scheme_data.description,
                is_active=True,
                created_by=created_by,
                owner_id=owner_id,
                created_by_role=creator_role
            )
            
            self.db.add(db_scheme)
            self.db.commit()
            self.db.refresh(db_scheme)
            
            return db_scheme
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create scheme: {str(e)}"
            )
    
    def get_scheme_by_id(self, scheme_id: int) -> Optional[Scheme]:
        """Get scheme by ID"""
        return self.db.query(Scheme).filter(Scheme.id == scheme_id).first()
    
    def get_schemes(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
        current_user_role: Optional[str] = None,
        filter_user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Tuple[List[Scheme], int]:
        """Get paginated list of schemes with comprehensive filtering"""
        query = self.db.query(Scheme)
        
        # If current_user_id is not provided, return empty result for security
        if not current_user_id or not current_user_role:
            return [], 0
        
        # Apply user-based access control using base service
        query = self.apply_user_access_filter(query, Scheme, current_user_id, current_user_role, filter_user_id)
        
        # Apply date filters
        if from_date is not None:
            query = query.filter(Scheme.created_at >= from_date)
        
        if to_date is not None:
            query = query.filter(Scheme.created_at <= to_date)
        
        # Apply status filter - default to active schemes only
        if is_active is not None:
            query = query.filter(Scheme.is_active == is_active)
        else:
            # Default behavior: only show active schemes
            query = query.filter(Scheme.is_active == True)
        
        # Apply search filter
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Scheme.name.ilike(search_term),
                    Scheme.description.ilike(search_term)
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(Scheme.created_at.desc())
        
        total = query.count()
        schemes = query.offset(skip).limit(limit).all()
        
        return schemes, total
    
    def get_schemes_with_token(
        self,
        token: str,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        filter_user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Tuple[List[Scheme], int]:
        """Get schemes using JWT token for authentication"""
        current_user_id, current_user_role = self.extract_user_from_token(token)
        
        return self.get_schemes(
            skip=skip,
            limit=limit,
            is_active=is_active,
            search=search,
            current_user_id=current_user_id,
            current_user_role=current_user_role,
            filter_user_id=filter_user_id,
            from_date=from_date,
            to_date=to_date
        )
    
    def transfer_scheme_ownership(self, scheme_id: int, new_owner_id: int, current_user_id: int, current_user_role: str) -> Scheme:
        """Transfer ownership of a scheme to another user"""
        scheme = self.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Check if current user can transfer ownership
        ownership_options = RoleHierarchy.get_scheme_ownership_options(current_user_role)
        if not ownership_options["can_transfer_ownership"] and scheme.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to transfer ownership of this scheme"
            )
        
        # Verify new owner exists
        new_owner = self.db.query(User).filter(User.id == new_owner_id).first()
        if not new_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New owner user not found"
            )
        
        # Transfer ownership
        scheme.transfer_ownership(new_owner_id)
        self.db.commit()
        self.db.refresh(scheme)
        
        return scheme
    
    def update_scheme_status(self, scheme_id: int, is_active: bool) -> Scheme:
        """Activate or deactivate a scheme"""
        scheme = self.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        scheme.is_active = is_active
        scheme.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(scheme)
        
        return scheme
    
    def update_scheme(self, scheme_id: int, scheme_data: SchemeUpdate) -> Scheme:
        """Update an existing scheme"""
        scheme = self.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Update fields if provided
        if scheme_data.name is not None:
            # Check if new name already exists (excluding current scheme)
            existing = self.db.query(Scheme).filter(
                and_(
                    Scheme.name == scheme_data.name,
                    Scheme.id != scheme_id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Scheme with name '{scheme_data.name}' already exists"
                )
            
            scheme.name = scheme_data.name
        
        if scheme_data.description is not None:
            scheme.description = scheme_data.description
            
        if scheme_data.is_active is not None:
            scheme.is_active = scheme_data.is_active
        
        scheme.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(scheme)
            return scheme
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update scheme: {str(e)}"
            )
    
    def delete_scheme(self, scheme_id: int) -> bool:
        """Delete a scheme (soft delete by deactivating)"""
        scheme = self.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Check if scheme has active commissions
        active_commissions = self.db.query(Commission).filter(
            and_(
                Commission.scheme_id == scheme_id,
                Commission.is_active == True
            )
        ).count()
        
        if active_commissions > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete scheme with active commissions. Deactivate commissions first."
            )
        
        # Soft delete by deactivating
        scheme.is_active = False
        scheme.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def share_scheme_with_user(self, scheme_id: int, target_user_id: int, current_user_id: int, current_user_role: str) -> Scheme:
        """Share scheme with specific user"""
        scheme = self.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Check if current user can share this scheme
        if not scheme.can_be_edited_by_user(current_user_id, current_user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to share this scheme"
            )
        
        # Verify target user exists
        target_user = self.db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        # Note: Since we removed shared_with_users column, this is a placeholder
        # In a real implementation, you might use a separate sharing table
        # For now, just return the scheme without modification
        scheme.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(scheme)
        
        return scheme
    
    def remove_scheme_user_access(self, scheme_id: int, target_user_id: int, current_user_id: int, current_user_role: str) -> Scheme:
        """Remove user access from shared scheme"""
        scheme = self.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Check if current user can modify sharing for this scheme
        if not scheme.can_be_edited_by_user(current_user_id, current_user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify sharing for this scheme"
            )
        
        # Note: Since we removed shared_with_users column, this is a placeholder
        # In a real implementation, you might use a separate sharing table
        # For now, just return the scheme without modification
        scheme.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(scheme)
        
        return scheme


class ServiceOperatorService:
    """Service class for service operator management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_operator(self, operator_data: ServiceOperatorCreate) -> ServiceOperator:
        """Create a new service operator"""
        # Check for duplicate operator name within same service type
        existing = self.db.query(ServiceOperator).filter(
            and_(
                ServiceOperator.name == operator_data.name,
                ServiceOperator.service_type == operator_data.service_type
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operator '{operator_data.name}' already exists for service '{operator_data.service_type}'"
            )
        
        db_operator = ServiceOperator(**operator_data.dict())
        self.db.add(db_operator)
        self.db.commit()
        self.db.refresh(db_operator)
        
        return db_operator
    
    def get_operators_by_service(self, service_type: ServiceTypeEnum) -> List[ServiceOperator]:
        """Get all operators for a specific service type"""
        return self.db.query(ServiceOperator).filter(
            and_(
                ServiceOperator.service_type == service_type,
                ServiceOperator.is_active == True
            )
        ).all()
    
    def get_or_create_operator(self, name: str, service_type: ServiceTypeEnum) -> ServiceOperator:
        """Get existing operator or create new one"""
        # Convert ServiceTypeEnum to string value for comparison
        service_type_value = service_type if isinstance(service_type, str) else service_type.value
        
        operator = self.db.query(ServiceOperator).filter(
            and_(
                ServiceOperator.name == name,
                ServiceOperator.service_type == service_type_value
            )
        ).first()
        
        if not operator:
            operator_data = ServiceOperatorCreate(name=name, service_type=service_type)
            operator = self.create_operator(operator_data)
        
        return operator


class CommissionService(BaseService):
    """Service class for commission management operations"""
    
    def __init__(self, db: Session, token_service: Optional[TokenService] = None):
        super().__init__(db, token_service)
        # Don't create new instances to avoid circular dependencies
        self._scheme_service = None
        self._operator_service = None
    
    @property
    def scheme_service(self):
        """Lazy initialization of scheme service"""
        if self._scheme_service is None:
            self._scheme_service = SchemeService(self.db, self.token_service)
        return self._scheme_service
    
    @property
    def operator_service(self):
        """Lazy initialization of operator service"""
        if self._operator_service is None:
            self._operator_service = ServiceOperatorService(self.db)
        return self._operator_service
    
    def create_commission(
        self, 
        scheme_id: int, 
        commission_data: CommissionCreate, 
        user_id: Optional[int] = None, 
        user_role: Optional[str] = None,
        token: Optional[str] = None
    ) -> Commission:
        """Create a new commission structure with role-based validation"""
        
        # Extract user info from token if not provided
        if not user_id or not user_role:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required: provide token or user credentials"
                )
            user_id, user_role = self.extract_user_from_token(token)
        
        # Validate scheme exists and user can access it
        scheme = self.scheme_service.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Check if user can access this scheme
        if not scheme.can_be_accessed_by_user(user_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this scheme"
            )
        
        # Validate user can set commissions
        permissions = RoleHierarchy.get_role_permissions(user_role)
        if not permissions.get("commissions.create", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' is not authorized to create commissions"
            )
        
        # Validate operator exists
        operator = self.db.query(ServiceOperator).filter(
            ServiceOperator.id == commission_data.operator_id
        ).first()
        
        if not operator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service operator not found"
            )
        
        # Check for existing commission
        existing = self.db.query(Commission).filter(
            and_(
                Commission.scheme_id == scheme_id,
                Commission.operator_id == commission_data.operator_id,
                Commission.service_type == commission_data.service_type
            )
        ).first()
        
        if existing:
            # For bulk operations, we want to allow updates instead of errors
            # This flag can be passed to indicate update behavior is desired
            allow_update = getattr(commission_data, 'allow_update', False)
            if not allow_update:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Commission already exists for this scheme, operator, and service"
                )
        
        # Validate user can only set commissions for roles they can manage
        commission_dict = commission_data.dict()
        
        # Extract only role-related commission fields for validation
        role_fields = ["admin", "whitelabel", "masterdistributor", "distributor", "retailer", "customer"]
        role_commission_data = {field: commission_dict.get(field, 0) for field in role_fields if field in commission_dict}
        
        role_permission_errors = RoleHierarchy.validate_commission_role_permissions(user_role, role_commission_data)
        
        if role_permission_errors:
            # Get the first error to show
            first_error_role = list(role_permission_errors.keys())[0]
            first_error_message = role_permission_errors[first_error_role]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=first_error_message
            )
        
        # Validate commission hierarchy using the new validation method
        if not RoleHierarchy.validate_commission_hierarchy(role_commission_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Commission hierarchy violation: parent role commission must be >= child role commission"
            )
        
        # Create commission with transaction management
        try:
            commission_dict = commission_data.dict(exclude={'slabs'})
            db_commission = Commission(scheme_id=scheme_id, **commission_dict)
            
            self.db.add(db_commission)
            self.db.commit()
            self.db.refresh(db_commission)
            
            # Create AEPS slabs if provided
            if self._is_aeps_service(commission_data.service_type) and commission_data.slabs:
                for slab_data in commission_data.slabs:
                    # Use model_dump() instead of dict() for Pydantic v2 compatibility
                    slab_dict = slab_data.model_dump() if hasattr(slab_data, 'model_dump') else slab_data.dict()
                    db_slab = CommissionSlab(
                        commission_id=db_commission.id,
                        **slab_dict
                    )
                    self.db.add(db_slab)
                
                self.db.commit()
            
            return db_commission
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create commission: {str(e)}"
            )
    
    def update_commission(
        self, 
        commission_id: int, 
        commission_data: CommissionUpdate, 
        user_id: Optional[int] = None, 
        user_role: Optional[str] = None,
        token: Optional[str] = None
    ) -> Commission:
        """Update an existing commission structure with role-based validation"""
        
        # Extract user info from token if not provided
        if not user_id or not user_role:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required: provide token or user credentials"
                )
            user_id, user_role = self.extract_user_from_token(token)
        
        # Get existing commission
        commission = self.db.query(Commission).filter(Commission.id == commission_id).first()
        if not commission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commission not found"
            )
        
        # Validate scheme exists and user can access it
        scheme = self.scheme_service.get_scheme_by_id(commission.scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated scheme not found"
            )
        
        # Check if user can access this scheme
        if not scheme.can_be_accessed_by_user(user_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this scheme"
            )
        
        # Validate user can update commissions
        permissions = RoleHierarchy.get_role_permissions(user_role)
        if not permissions.get("commissions.update", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' is not authorized to update commissions"
            )
        
        # Get editable fields based on user role
        editable_fields = RoleHierarchy.get_editable_commission_fields(user_role)
        
        # Define always-editable fields that any user can modify
        always_editable = ['commission_type', 'service_type', 'operator_id', 'is_active']
        
        # Combine role-based editable fields with always-editable fields
        all_editable_fields = set(editable_fields + always_editable)
        
        # Filter update data to only include editable fields
        update_data = commission_data.dict(exclude_unset=True)
        
        # Add debug logging
        print(f"DEBUG UPDATE: User role: {user_role}")
        print(f"DEBUG UPDATE: Editable role fields: {editable_fields}")
        print(f"DEBUG UPDATE: All editable fields: {all_editable_fields}")
        print(f"DEBUG UPDATE: Update data keys: {list(update_data.keys())}")
        
        filtered_update_data = {
            field: value for field, value in update_data.items()
            if field in all_editable_fields
        }
        
        print(f"DEBUG UPDATE: Filtered update data: {filtered_update_data}")
        
        # Check if user can edit any commission role fields (if trying to update them)
        role_fields = ["admin", "whitelabel", "masterdistributor", "distributor", "retailer", "customer"]
        role_updates = {k: v for k, v in update_data.items() if k in role_fields}
        
        if role_updates and not any(field in editable_fields for field in role_updates.keys()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role ({user_role}) cannot edit commission role fields: {list(role_updates.keys())}"
            )
        
        if not filtered_update_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role ({user_role}) cannot edit any commission fields. Available fields: {list(all_editable_fields)}"
            )
        
        # Validate commission hierarchy if commission values are being updated
        role_fields = ["admin", "whitelabel", "masterdistributor", "distributor", "retailer", "customer"]
        role_commission_data = {}
        
        # Get current values and apply updates
        for field in role_fields:
            if field in filtered_update_data:
                role_commission_data[field] = float(filtered_update_data[field])
            else:
                current_value = getattr(commission, field, 0)
                role_commission_data[field] = float(current_value) if current_value is not None else 0
        
        # Validate role permissions for the updated values
        role_permission_errors = RoleHierarchy.validate_commission_role_permissions(user_role, role_commission_data)
        
        if role_permission_errors:
            first_error_role = list(role_permission_errors.keys())[0]
            first_error_message = role_permission_errors[first_error_role]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=first_error_message
            )
        
        # Validate commission hierarchy
        if not RoleHierarchy.validate_commission_hierarchy(role_commission_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Commission hierarchy violation: parent role commission must be >= child role commission"
            )
        
        # Update commission with transaction management
        try:
            # Update regular commission fields
            for field, value in filtered_update_data.items():
                if field != 'slabs':  # Handle slabs separately
                    setattr(commission, field, value)
            
            # Handle AEPS slabs if provided
            if 'slabs' in filtered_update_data and self._is_aeps_service(commission.service_type):
                # Remove existing slabs
                self.db.query(CommissionSlab).filter(
                    CommissionSlab.commission_id == commission_id
                ).delete()
                
                # Add new slabs
                for slab_data in filtered_update_data['slabs']:
                    if isinstance(slab_data, dict):
                        db_slab = CommissionSlab(
                            commission_id=commission_id,
                            **slab_data
                        )
                    else:
                        # Use model_dump() instead of dict() for Pydantic v2 compatibility
                        slab_dict = slab_data.model_dump() if hasattr(slab_data, 'model_dump') else slab_data.dict()
                        db_slab = CommissionSlab(
                            commission_id=commission_id,
                            **slab_dict
                        )
                    self.db.add(db_slab)
            
            self.db.commit()
            self.db.refresh(commission)
            
            return commission
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update commission: {str(e)}"
            )

    def get_commissions_by_scheme_and_service(
        self, 
        scheme_id: int, 
        service_type: ServiceTypeEnum,
        current_user_id: Optional[int] = None,
        current_user_role: Optional[str] = None
    ) -> List[Commission]:
        """Get all commissions for a scheme and service type with access control"""
        
        # Security: Ensure user authentication
        if not current_user_id or not current_user_role:
            return []
        
        # Check if user has access to this scheme
        scheme = self.scheme_service.get_scheme_by_id(scheme_id)
        if not scheme:
            return []
        
        # Validate scheme access using role hierarchy
        user = self.db.query(User).filter(User.id == current_user_id).first()
        if not user or not RoleHierarchy.can_user_access_scheme(user, scheme):
            return []
        
        from sqlalchemy.orm import joinedload
        
        return self.db.query(Commission).options(
            joinedload(Commission.slabs),
            joinedload(Commission.operator)
        ).filter(
            and_(
                Commission.scheme_id == scheme_id,
                Commission.service_type == service_type,
                Commission.is_active == True
            )
        ).all()
    
    def get_commissions(
        self,
        skip: int = 0,
        limit: int = 100,
        scheme_id: Optional[int] = None,
        service_type: Optional[ServiceTypeEnum] = None,
        is_active: Optional[bool] = None,
        current_user_id: Optional[int] = None,
        current_user_role: Optional[str] = None,
        filter_user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Commission], int]:
        """Get paginated list of commissions with comprehensive filtering"""
        from sqlalchemy.orm import joinedload
        
        query = self.db.query(Commission).join(Scheme)
        
        # Eagerly load slabs for AEPS services
        query = query.options(
            joinedload(Commission.slabs),
            joinedload(Commission.operator)
        )
        
        # Security: Ensure user authentication
        if not current_user_id or not current_user_role:
            return [], 0
        
        # Apply scheme-level access control using base service
        query = self.apply_user_access_filter(query, Scheme, current_user_id, current_user_role, filter_user_id)
        
        # Filter by specific scheme
        if scheme_id is not None:
            query = query.filter(Commission.scheme_id == scheme_id)
        
        # Filter by service type
        if service_type is not None:
            query = query.filter(Commission.service_type == service_type)
        
        # Filter by status
        if is_active is not None:
            query = query.filter(Commission.is_active == is_active)
        
        # Apply date filters
        if from_date is not None:
            query = query.filter(Commission.created_at >= from_date)
        
        if to_date is not None:
            query = query.filter(Commission.created_at <= to_date)
        
        # Apply search filter (search in scheme name or operator name)
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.join(ServiceOperator).filter(
                or_(
                    Scheme.name.ilike(search_term),
                    ServiceOperator.name.ilike(search_term)
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(Commission.created_at.desc())
        
        total = query.count()
        commissions = query.offset(skip).limit(limit).all()
        
        return commissions, total
    
    def get_commissions_with_token(
        self,
        token: str,
        skip: int = 0,
        limit: int = 100,
        scheme_id: Optional[int] = None,
        service_type: Optional[ServiceTypeEnum] = None,
        is_active: Optional[bool] = None,
        filter_user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Commission], int]:
        """Get commissions using JWT token for authentication"""
        current_user_id, current_user_role = self.extract_user_from_token(token)
        
        return self.get_commissions(
            skip=skip,
            limit=limit,
            scheme_id=scheme_id,
            service_type=service_type,
            is_active=is_active,
            current_user_id=current_user_id,
            current_user_role=current_user_role,
            filter_user_id=filter_user_id,
            from_date=from_date,
            to_date=to_date,
            search=search
        )
    
    def bulk_create_commissions(
        self, 
        scheme_id: int, 
        bulk_data: BulkCommissionCreate,
        user_id: int,
        user_role: str
    ) -> Dict[str, Any]:
        """Bulk create/update commissions for a service"""
        # Check scheme access
        scheme = self.scheme_service.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Verify user can access this scheme
        role_hierarchy = RoleHierarchy()
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not role_hierarchy.can_user_access_scheme(user, scheme):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this scheme"
            )
        
        successful_entries = 0
        failed_entries = 0
        updated_entries = 0
        created_entries = 0
        errors = []
        
        for entry in bulk_data.entries:
            try:
                if self._is_aeps_service(bulk_data.service):
                    # Handle AEPS with slabs
                    operation_result = self._create_or_update_aeps_commission(
                        scheme_id, entry, bulk_data.service, user_role, user_id
                    )
                else:
                    # Handle regular commission
                    operation_result = self._create_or_update_regular_commission(
                        scheme_id, entry, bulk_data.service, user_role, user_id
                    )
                
                successful_entries += 1
                if operation_result == "updated":
                    updated_entries += 1
                else:
                    created_entries += 1
                
            except Exception as e:
                failed_entries += 1
                errors.append(f"Entry '{entry.operator}': {str(e)}")
        
        return {
            "service": bulk_data.service,
            "total_entries": len(bulk_data.entries),
            "successful_entries": successful_entries,
            "failed_entries": failed_entries,
            "created_entries": created_entries,
            "updated_entries": updated_entries,
            "errors": errors
        }

    def bulk_update_commissions(
        self, 
        scheme_id: int, 
        bulk_data: BulkCommissionCreate,
        user_id: int,
        user_role: str
    ) -> Dict[str, Any]:
        """Bulk update existing commissions for a service"""
        # Check scheme access
        scheme = self.scheme_service.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Verify user can access this scheme
        role_hierarchy = RoleHierarchy()
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not role_hierarchy.can_user_access_scheme(user, scheme):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this scheme"
            )
        
        successful_entries = 0
        failed_entries = 0
        skipped_entries = 0
        errors = []
        
        for entry in bulk_data.entries:
            try:
                # Convert service_type to enum if it's a string
                service_type = bulk_data.service
                if isinstance(service_type, str):
                    try:
                        service_type = ServiceTypeEnum(service_type)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid service type: {service_type}"
                        )
                
                # Get operator
                operator = self.operator_service.get_or_create_operator(
                    entry.operator, service_type
                )
                
                # Check if commission exists - use commission_id if provided, otherwise lookup by operator
                existing_commission = None
                
                if hasattr(entry, 'commission_id') and entry.commission_id:
                    # Use commission_id if provided (for frontend updates)
                    existing_commission = self.db.query(Commission).filter(
                        Commission.id == entry.commission_id,
                        Commission.scheme_id == scheme_id
                    ).first()
                else:
                    # Fallback to lookup by operator and service type
                    existing_commission = self.db.query(Commission).filter(
                        and_(
                            Commission.scheme_id == scheme_id,
                            Commission.operator_id == operator.id,
                            Commission.service_type == service_type
                        )
                    ).first()
                
                if existing_commission:
                    # Update existing commission (removed superadmin field)
                    if self._is_aeps_service(service_type):
                        commission_data = CommissionUpdate(
                            commission_type=entry.commission_type,
                            slabs=entry.slabs if hasattr(entry, 'slabs') and entry.slabs else []
                        )
                    else:
                        commission_data = CommissionUpdate(
                            commission_type=entry.commission_type,
                            admin=getattr(entry, 'admin', 0),
                            whitelabel=getattr(entry, 'whitelabel', 0),
                            masterdistributor=getattr(entry, 'masterdistributor', 0),
                            distributor=getattr(entry, 'distributor', 0),
                            retailer=getattr(entry, 'retailer', 0),
                            customer=getattr(entry, 'customer', 0)
                        )
                    
                    print(f"DEBUG BULK UPDATE: Updating commission {existing_commission.id} with data: {commission_data.dict()}")
                    
                    self.update_commission(
                        existing_commission.id, 
                        commission_data, 
                        user_id=user_id, 
                        user_role=user_role
                    )
                    successful_entries += 1
                else:
                    # Skip entries that don't exist
                    skipped_entries += 1
                    errors.append(f"Entry '{entry.operator}': Commission does not exist, skipping update")
                
            except Exception as e:
                failed_entries += 1
                errors.append(f"Entry '{entry.operator}': {str(e)}")
        
        return {
            "service": bulk_data.service,
            "total_entries": len(bulk_data.entries),
            "successful_entries": successful_entries,
            "failed_entries": failed_entries,
            "skipped_entries": skipped_entries,
            "updated_entries": successful_entries,
            "created_entries": 0,
            "errors": errors
        }
    
    def _is_aeps_service(self, service_type) -> bool:
        """Helper method to check if service type is AEPS"""
        if isinstance(service_type, str):
            return service_type == "aeps"
        return service_type == ServiceTypeEnum.AEPS

    def export_commissions_csv(
        self, 
        scheme_id: int, 
        service_type: ServiceTypeEnum
    ) -> str:
        """Export commissions to CSV format"""
        scheme = self.scheme_service.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        commissions = self.get_commissions_by_scheme_and_service(scheme_id, service_type)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        if self._is_aeps_service(service_type):
            writer.writerow([
                'Operator', 'Commission Type', 'Slab Min', 'Slab Max',
                'Admin', 'Whitelabel', 'Master Distributor',
                'Distributor', 'Retailer', 'Customer'
            ])
        else:
            writer.writerow([
                'Operator', 'Commission Type',
                'Admin', 'Whitelabel', 'Master Distributor',
                'Distributor', 'Retailer', 'Customer'
            ])
        
        # Write data
        for commission in commissions:
            if self._is_aeps_service(service_type) and commission.slabs:
                for slab in commission.slabs:
                    writer.writerow([
                        commission.operator.name,
                        commission.commission_type.value,
                        slab.slab_min,
                        slab.slab_max,
                        slab.admin,
                        slab.whitelabel,
                        slab.masterdistributor,
                        slab.distributor,
                        slab.retailer,
                        slab.customer
                    ])
            else:
                writer.writerow([
                    commission.operator.name,
                    commission.commission_type.value,
                    commission.admin,
                    commission.whitelabel,
                    commission.masterdistributor,
                    commission.distributor,
                    commission.retailer,
                    commission.customer
                ])
        
        return output.getvalue()
    
    def calculate_commission_for_user(
        self, 
        scheme_id: int, 
        operator_id: int, 
        service_type: ServiceTypeEnum,
        user_role: str,
        amount: Decimal
    ) -> Dict[str, Any]:
        """Calculate commission for a specific user role and amount"""
        commission = self.db.query(Commission).filter(
            and_(
                Commission.scheme_id == scheme_id,
                Commission.operator_id == operator_id,
                Commission.service_type == service_type,
                Commission.is_active == True
            )
        ).first()
        
        if not commission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commission structure not found"
            )
        
        commission_rate = 0.0
        
        if self._is_aeps_service(service_type):
            # Find applicable slab
            slab = self.db.query(CommissionSlab).filter(
                and_(
                    CommissionSlab.commission_id == commission.id,
                    CommissionSlab.slab_min <= amount,
                    CommissionSlab.slab_max >= amount,
                    CommissionSlab.is_active == True
                )
            ).first()
            
            if slab:
                commission_rate = slab.get_commission_for_role(user_role)
        else:
            commission_rate = commission.get_commission_for_role(user_role)
        
        # Calculate final amount
        if commission.commission_type == CommissionTypeEnum.PERCENT:
            commission_amount = (amount * Decimal(str(commission_rate))) / 100
        else:  # FLAT
            commission_amount = Decimal(str(commission_rate))
        
        return {
            "scheme_id": scheme_id,
            "operator_id": operator_id,
            "service_type": service_type.value,
            "user_role": user_role,
            "amount": float(amount),
            "commission_rate": commission_rate,
            "commission_type": commission.commission_type.value,
            "commission_amount": float(commission_amount)
        }
    
    def _validate_commission_hierarchy(self, commission_data: CommissionCreate) -> bool:
        """Validate commission hierarchy"""
        hierarchy = [
            commission_data.admin,
            commission_data.whitelabel,
            commission_data.masterdistributor,
            commission_data.distributor,
            commission_data.retailer,
            commission_data.customer
        ]
        
        for i in range(len(hierarchy) - 1):
            if hierarchy[i] < hierarchy[i + 1]:
                return False
        return True
    
    def _create_or_update_regular_commission(
        self, 
        scheme_id: int, 
        entry: CommissionEntry, 
        service_type,  # Accept both string and enum
        user_role: str,
        user_id: int
    ) -> str:
        """Create or update regular commission entry"""
        # Convert service_type to enum if it's a string
        if isinstance(service_type, str):
            try:
                service_type = ServiceTypeEnum(service_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid service type: {service_type}"
                )
        
        # Get or create operator
        operator = self.operator_service.get_or_create_operator(
            entry.operator, service_type
        )
        
        # Check if commission already exists
        existing_commission = self.db.query(Commission).filter(
            and_(
                Commission.scheme_id == scheme_id,
                Commission.operator_id == operator.id,
                Commission.service_type == service_type
            )
        ).first()
        
        if existing_commission:
            # Update existing commission
            commission_data = CommissionUpdate(
                commission_type=entry.commission_type,
                admin=entry.admin,
                whitelabel=entry.whitelabel,
                masterdistributor=entry.masterdistributor,
                distributor=entry.distributor,
                retailer=entry.retailer,
                customer=entry.customer
            )
            
            self.update_commission(
                existing_commission.id, 
                commission_data, 
                user_id=user_id, 
                user_role=user_role
            )
            return "updated"
        else:
            # Create new commission
            commission_data = CommissionCreate(
                operator_id=operator.id,
                service_type=service_type,
                commission_type=entry.commission_type,
                admin=entry.admin,
                whitelabel=entry.whitelabel,
                masterdistributor=entry.masterdistributor,
                distributor=entry.distributor,
                retailer=entry.retailer,
                customer=entry.customer
            )
            
            self.create_commission(scheme_id, commission_data, user_id=user_id, user_role=user_role)
            return "created"
    
    def _create_or_update_aeps_commission(
        self, 
        scheme_id: int, 
        entry: CommissionEntry, 
        service_type,
        user_role: str,
        user_id: int
    ) -> str:
        """Create or update AEPS commission entry with slabs"""
        # Convert service_type to enum if it's a string
        if isinstance(service_type, str):
            try:
                service_type = ServiceTypeEnum(service_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid service type: {service_type}"
                )
        
        # Get or create operator
        operator = self.operator_service.get_or_create_operator(
            entry.operator, service_type
        )
        
        # Check if commission already exists
        existing_commission = self.db.query(Commission).filter(
            and_(
                Commission.scheme_id == scheme_id,
                Commission.operator_id == operator.id,
                Commission.service_type == service_type
            )
        ).first()
        
        if existing_commission:
            # Update existing AEPS commission with slabs
            commission_data = CommissionUpdate(
                commission_type=entry.commission_type,
                slabs=entry.slabs if hasattr(entry, 'slabs') and entry.slabs else []
            )
            
            self.update_commission(
                existing_commission.id, 
                commission_data, 
                user_id=user_id, 
                user_role=user_role
            )
            return "updated"
        else:
            # Create new AEPS commission
            commission_data = CommissionCreate(
                operator_id=operator.id,
                service_type=service_type,
                commission_type=entry.commission_type,
                slabs=entry.slabs if hasattr(entry, 'slabs') and entry.slabs else []
            )
            
            self.create_commission(scheme_id, commission_data, user_id=user_id, user_role=user_role)
            return "created"

    def _create_regular_commission(
        self, 
        scheme_id: int, 
        entry: CommissionEntry, 
        service_type,  # Accept both string and enum
        user_role: str,
        user_id: int
    ) -> None:
        """Create regular commission entry"""
        # Convert service_type to enum if it's a string
        if isinstance(service_type, str):
            try:
                service_type = ServiceTypeEnum(service_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid service type: {service_type}"
                )
        
        # Get or create operator
        operator = self.operator_service.get_or_create_operator(
            entry.operator, service_type
        )
        
        # Create commission data
        commission_data = CommissionCreate(
            operator_id=operator.id,
            service_type=service_type,
            commission_type=entry.commission_type,
            admin=entry.admin,
            whitelabel=entry.whitelabel,
            masterdistributor=entry.masterdistributor,
            distributor=entry.distributor,
            retailer=entry.retailer,
            customer=entry.customer
        )
        
        # Get user_id from the current session and use proper validation
        self.create_commission(scheme_id, commission_data, user_id=user_id, user_role=user_role)
    
    def _create_aeps_commission(
        self, 
        scheme_id: int, 
        entry: AEPSCommissionEntry, 
        service_type,  # Accept both string and enum
        user_role: str,
        user_id: int
    ) -> None:
        """Create AEPS commission entry with slabs"""
        # Convert service_type to enum if it's a string
        if isinstance(service_type, str):
            try:
                service_type = ServiceTypeEnum(service_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid service type: {service_type}"
                )
        
        # Get or create operator
        operator = self.operator_service.get_or_create_operator(
            entry.operator, service_type
        )
        
        # Convert slabs to CommissionSlabCreate objects
        slabs = []
        for slab in entry.slabs:
            slab_create = {
                'slab_min': slab.slab_min,
                'slab_max': slab.slab_max,
                'admin': slab.admin,
                'whitelabel': slab.whitelabel,
                'masterdistributor': slab.md,
                'distributor': slab.distributor,
                'retailer': slab.retailer,
                'customer': slab.customer
            }
            slabs.append(slab_create)
        
        # Create commission data
        commission_data = CommissionCreate(
            operator_id=operator.id,
            service_type=service_type,
            commission_type=entry.commission_type,
            slabs=slabs
        )
        
        # Pass user parameters for proper validation
        self.create_commission(scheme_id, commission_data, user_id=user_id, user_role=user_role)

    # ==================== COMMISSION SLAB MANAGEMENT ====================
    
    def get_commission_slabs(self, commission_id: int) -> List[CommissionSlab]:
        """Get all slabs for a commission"""
        commission = self.db.query(Commission).filter(Commission.id == commission_id).first()
        if not commission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commission not found"
            )
        
        # Only AEPS commissions have slabs
        if not self._is_aeps_service(commission.service_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slabs are only available for AEPS commissions"
            )
        
        return self.db.query(CommissionSlab).filter(
            CommissionSlab.commission_id == commission_id,
            CommissionSlab.is_active == True
        ).order_by(CommissionSlab.slab_min).all()
    
    def create_commission_slab(self, commission_id: int, slab_data: CommissionSlabCreate) -> CommissionSlab:
        """Create a new commission slab"""
        # Validate commission exists and is AEPS
        commission = self.db.query(Commission).filter(
            Commission.id == commission_id
        ).first()
        if not commission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commission not found"
            )
        
        if not self._is_aeps_service(commission.service_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slabs can only be created for AEPS commissions"
            )
        
        # Check for overlapping slabs
        existing_slabs = self.get_commission_slabs(commission_id)
        for existing in existing_slabs:
            if (slab_data.slab_min < existing.slab_max and 
                slab_data.slab_max > existing.slab_min):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slab range overlaps with existing slab"
                )
        
        # Create new slab
        slab_dict = slab_data.dict()
        slab_dict['commission_id'] = commission_id
        db_slab = CommissionSlab(**slab_dict)
        self.db.add(db_slab)
        self.db.commit()
        self.db.refresh(db_slab)
        
        return db_slab
    
    def update_commission_slab(self, slab_id: int, slab_data: CommissionSlabCreate) -> CommissionSlab:
        """Update an existing commission slab"""
        db_slab = self.db.query(CommissionSlab).filter(CommissionSlab.id == slab_id).first()
        if not db_slab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commission slab not found"
            )
        
        # Check for overlapping slabs (excluding current slab)
        existing_slabs = self.db.query(CommissionSlab).filter(
            CommissionSlab.commission_id == db_slab.commission_id,
            CommissionSlab.id != slab_id,
            CommissionSlab.is_active == True
        ).all()
        
        for existing in existing_slabs:
            if (slab_data.slab_min < existing.slab_max and 
                slab_data.slab_max > existing.slab_min):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slab range overlaps with existing slab"
                )
        
        # Update slab
        update_data = slab_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_slab, field, value)
        
        self.db.commit()
        self.db.refresh(db_slab)
        
        return db_slab
    
    def delete_commission_slab(self, slab_id: int) -> bool:
        """Delete (deactivate) a commission slab"""
        db_slab = self.db.query(CommissionSlab).filter(CommissionSlab.id == slab_id).first()
        if not db_slab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commission slab not found"
            )
        
        # Soft delete by setting is_active to False
        db_slab.is_active = False
        self.db.commit()
        
        return True