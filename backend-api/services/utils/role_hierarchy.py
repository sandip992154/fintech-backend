"""
Role Hierarchy Utilities for Commission Management
"""
from typing import List, Dict, Optional, Set
from enum import Enum

class RoleLevel(Enum):
    """Role hierarchy levels"""
    SUPER_ADMIN = 0
    ADMIN = 1  
    WHITELABEL = 2
    MDS = 3  # Master Distributor
    DISTRIBUTOR = 4
    RETAILER = 5
    CUSTOMER = 6

class RoleHierarchy:
    """Utility class for role hierarchy operations"""
    
    # Role hierarchy mapping
    ROLE_HIERARCHY = {
        "super_admin": RoleLevel.SUPER_ADMIN,
        "superadmin": RoleLevel.SUPER_ADMIN,  # Support both variants
        "admin": RoleLevel.ADMIN,
        "whitelabel": RoleLevel.WHITELABEL,
        "mds": RoleLevel.MDS,
        "masterdistributor": RoleLevel.MDS,  # Support both variants
        "distributor": RoleLevel.DISTRIBUTOR,
        "retailer": RoleLevel.RETAILER,
        "customer": RoleLevel.CUSTOMER
    }
    
    # Reverse mapping for display purposes
    LEVEL_TO_ROLE = {v: k for k, v in ROLE_HIERARCHY.items() if not k.endswith('admin')}
    
    @classmethod
    def get_role_level(cls, role: str) -> int:
        """Get numeric level for a role"""
        if not isinstance(role, str):
            # Convert to string if it's not already a string
            print(f"DEBUG: Converting role from {type(role)} to string: {role}")
            role = str(role)
        
        print(f"DEBUG: Looking up role level for: '{role}'")
        role_enum = cls.ROLE_HIERARCHY.get(role.lower())
        level = role_enum.value if role_enum else 999
        
        print(f"DEBUG: Role '{role}' -> enum: {role_enum} -> level: {level}")
        
        if level == 999:
            print(f"WARNING: Unknown role '{role}' defaulting to level 999")
        return level
    
    @classmethod
    def can_manage_role(cls, manager_role: str, target_role: str) -> bool:
        """Check if manager_role can manage target_role"""
        # Ensure both parameters are strings
        if not isinstance(manager_role, str):
            manager_role = str(manager_role)
        if not isinstance(target_role, str):
            target_role = str(target_role)
            
        manager_level = cls.get_role_level(manager_role)
        target_level = cls.get_role_level(target_role)
        return manager_level < target_level
    
    @classmethod
    def get_manageable_roles(cls, role: str) -> List[str]:
        """Get list of roles that the given role can manage"""
        role_level = cls.get_role_level(role)
        manageable = []
        
        for role_name, level_enum in cls.ROLE_HIERARCHY.items():
            if level_enum.value > role_level:
                manageable.append(role_name)
        
        return manageable
    
    @classmethod
    def get_commission_fields(cls, user_role: str) -> List[str]:
        """Get list of commission fields user can edit based on their role"""
        manageable_roles = cls.get_manageable_roles(user_role)
        
        # Map role names to commission field names
        field_mapping = {
            "super_admin": "superadmin",
            "superadmin": "superadmin", 
            "admin": "admin",
            "whitelabel": "whitelabel",
            "mds": "masterdistributor",
            "masterdistributor": "masterdistributor",
            "distributor": "distributor",
            "retailer": "retailer",
            "customer": "customer"
        }
        
        commission_fields = []
        for role in manageable_roles:
            if role in field_mapping:
                commission_fields.append(field_mapping[role])
        
        return commission_fields
    
    @classmethod
    def validate_commission_hierarchy(cls, commission_data: Dict[str, float]) -> bool:
        """Validate that commission values follow hierarchy (parent >= child)"""
        # Define the order of roles in hierarchy
        hierarchy_order = [
            "superadmin", "admin", "whitelabel", "masterdistributor", 
            "distributor", "retailer", "customer"
        ]
        
        # Get values in hierarchy order, treating 0.0 as "not set" for optional fields
        present_roles = []
        present_values = []
        
        for role in hierarchy_order:
            if role in commission_data:
                value = commission_data[role]
                # Consider a value as "not set" if it's None, 0.0, or 0
                # This handles default values from Pydantic schemas
                if value is not None and value > 0:
                    present_roles.append(role)
                    present_values.append(value)
        
        # Check that each present level >= next present level
        for i in range(len(present_values) - 1):
            if present_values[i] < present_values[i + 1]:
                return False
        
        return True
    
    @classmethod
    def get_role_display_name(cls, role: str) -> str:
        """Get display-friendly role name"""
        display_names = {
            "super_admin": "Super Admin",
            "superadmin": "Super Admin",
            "admin": "Admin", 
            "whitelabel": "White Label",
            "mds": "Master Distributor",
            "masterdistributor": "Master Distributor",
            "distributor": "Distributor",
            "retailer": "Retailer",
            "customer": "Customer"
        }
        return display_names.get(role.lower(), role.title())
    
    @classmethod
    def get_role_permissions(cls, role: str) -> Dict[str, bool]:
        """Get role-based permissions for scheme and commission operations"""
        role_level = cls.get_role_level(role)
        
        permissions = {
            # Scheme permissions
            "schemes.create": role_level <= RoleLevel.WHITELABEL.value,
            "schemes.update": role_level <= RoleLevel.WHITELABEL.value,
            "schemes.delete": role_level <= RoleLevel.ADMIN.value,
            "schemes.view_all": role_level <= RoleLevel.ADMIN.value,
            
            # Commission permissions  
            "commissions.create": role_level <= RoleLevel.WHITELABEL.value,
            "commissions.update": role_level <= RoleLevel.WHITELABEL.value,
            "commissions.delete": role_level <= RoleLevel.ADMIN.value,
            
            # Operator permissions
            "operators.create": role_level <= RoleLevel.ADMIN.value,
            "operators.update": role_level <= RoleLevel.ADMIN.value,
            "operators.delete": role_level <= RoleLevel.SUPER_ADMIN.value,
        }
        
        return permissions
    
    @classmethod
    def can_set_commission_for_role(cls, user_role: str, target_role: str) -> bool:
        """Check if user can set commission for a specific target role"""
        user_level = cls.get_role_level(user_role)
        target_level = cls.get_role_level(target_role)
        
        print(f"DEBUG: can_set_commission_for_role - user: '{user_role}' (level {user_level}) -> target: '{target_role}' (level {target_level})")
        
        # Users can set commissions for their own role and roles below them in hierarchy
        # (higher level number = lower in hierarchy)
        can_set = user_level <= target_level
        print(f"DEBUG: Can set commission: {can_set}")
        return can_set
    
    @classmethod
    def validate_commission_role_permissions(cls, user_role: str, commission_data: Dict[str, float]) -> Dict[str, str]:
        """Validate which commission roles the user is allowed to set and return errors"""
        errors = {}
        
        print(f"DEBUG: validate_commission_role_permissions - user_role: '{user_role}'")
        print(f"DEBUG: commission_data: {commission_data}")
        
        # Check each commission role that has a value > 0
        for role, value in commission_data.items():
            print(f"DEBUG: Checking role '{role}' with value {value}")
            if value is not None and value > 0:
                can_set = cls.can_set_commission_for_role(user_role, role)
                if not can_set:
                    error_msg = f"You cannot set commission for '{role}' role"
                    errors[role] = error_msg
                    print(f"DEBUG: ERROR - {error_msg}")
                else:
                    print(f"DEBUG: OK - Can set commission for '{role}'")
        
        print(f"DEBUG: Final errors: {errors}")
        return errors
    
    @classmethod
    def filter_schemes_by_user(cls, schemes: List, user_id: int, user_role: str) -> List:
        """Filter schemes based on user ownership and permissions"""
        role_level = cls.get_role_level(user_role)
        
        # Super admin and admin can see all schemes
        if role_level <= RoleLevel.ADMIN.value:
            return schemes
        
        # Filter schemes based on user-based ownership and sharing
        accessible_schemes = []
        for scheme in schemes:
            if scheme.can_be_accessed_by_user(user_id, user_role):
                accessible_schemes.append(scheme)
        
        return accessible_schemes
    
    @classmethod
    def filter_editable_schemes(cls, schemes: List, user_id: int, user_role: str) -> List:
        """Filter schemes that user can edit"""
        editable_schemes = []
        for scheme in schemes:
            if scheme.can_be_edited_by_user(user_id, user_role):
                editable_schemes.append(scheme)
        
        return editable_schemes
    
    @classmethod
    def can_create_scheme(cls, user_role: str) -> bool:
        """Check if user role can create schemes"""
        role_level = cls.get_role_level(user_role)
        # Super admin, admin, and whitelabel can create schemes
        return role_level <= RoleLevel.WHITELABEL.value
    
    @classmethod
    def get_scheme_ownership_options(cls, user_role: str) -> Dict[str, bool]:
        """Get ownership and sharing options available to user role"""
        role_level = cls.get_role_level(user_role)
        
        return {
            "can_create": role_level <= RoleLevel.WHITELABEL.value,
            "can_transfer_ownership": role_level <= RoleLevel.ADMIN.value,
            "can_share_with_users": role_level <= RoleLevel.WHITELABEL.value,
            "can_share_with_roles": role_level <= RoleLevel.ADMIN.value,
            "can_delete_any": role_level <= RoleLevel.ADMIN.value,
            "can_view_all": role_level <= RoleLevel.ADMIN.value,
        }
    
    @classmethod
    def get_commission_validation_rules(cls, user_role: str) -> Dict[str, any]:
        """Get validation rules for commission based on user role"""
        manageable_fields = cls.get_commission_fields(user_role)
        
        return {
            "editable_fields": manageable_fields,
            "required_hierarchy": True,
            "min_value": 0.0,
            "max_value": 100.0 if user_role != "super_admin" else None
        }
    
    @classmethod
    def can_user_access_scheme(cls, user, scheme) -> bool:
        """Check if user can access a specific scheme"""
        if not user or not scheme:
            return False
        
        try:
            # Get user role name safely
            if hasattr(user, 'role') and user.role:
                if hasattr(user.role, 'name'):
                    user_role = user.role.name.lower()
                else:
                    user_role = str(user.role).lower()
            else:
                return False
            
            # Superadmin can access everything
            if user_role in ['super_admin', 'superadmin']:
                return True
                
            # Owner can access
            if hasattr(scheme, 'owner_id') and scheme.owner_id == user.id:
                return True
                
            # Creator can access
            if hasattr(scheme, 'created_by') and scheme.created_by == user.id:
                return True
                
            # Higher hierarchy roles can access based on scheme creator role
            if hasattr(scheme, 'created_by_role'):
                scheme_creator_role = str(scheme.created_by_role).lower()
                return cls.can_manage_role(user_role, scheme_creator_role)
                
            return False
            
        except Exception as e:
            print(f"Error in can_user_access_scheme: {e}")
            print(f"user: {user}, user.role: {getattr(user, 'role', None)}")
            print(f"scheme: {scheme}, scheme.created_by_role: {getattr(scheme, 'created_by_role', None)}")
            return False
        # Creator can access
        if hasattr(scheme, 'created_by') and scheme.created_by == user.id:
            return True
            
        # Role hierarchy access
        if hasattr(scheme, 'created_by_role') and scheme.created_by_role:
            return cls.can_manage_role(user_role, scheme.created_by_role)
            
        return False
    
    @classmethod
    def get_editable_commission_fields(cls, user_role: str) -> List[str]:
        """Get list of commission fields that user role can edit"""
        role_level = cls.get_role_level(user_role)
        
        # Super admin can edit all fields except superadmin (removed as requested)
        if role_level <= RoleLevel.SUPER_ADMIN.value:
            return ['admin', 'whitelabel', 'masterdistributor', 'distributor', 'retailer', 'customer']
        
        # Admin can edit admin and below
        elif role_level <= RoleLevel.ADMIN.value:
            return ['admin', 'whitelabel', 'masterdistributor', 'distributor', 'retailer', 'customer']
        
        # Whitelabel can edit whitelabel and below
        elif role_level <= RoleLevel.WHITELABEL.value:
            return ['whitelabel', 'masterdistributor', 'distributor', 'retailer', 'customer']
        
        # Master distributor can edit masterdistributor and below
        elif role_level <= RoleLevel.MDS.value:
            return ['masterdistributor', 'distributor', 'retailer', 'customer']
        
        # Distributor can edit distributor and below
        elif role_level <= RoleLevel.DISTRIBUTOR.value:
            return ['distributor', 'retailer', 'customer']
        
        # Retailer can edit retailer and below
        elif role_level <= RoleLevel.RETAILER.value:
            return ['retailer', 'customer']
        
        # Customer can only edit customer
        else:
            return ['customer']