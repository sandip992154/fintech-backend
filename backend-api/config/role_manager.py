"""
Role-based configuration and utilities for the Bandaru Pay API.
"""
from typing import List, Dict
from .constants import ROLE_HIERARCHY, VALID_PERMISSIONS

class RoleManager:
    @staticmethod
    def has_permission(user_role: str, required_role: str) -> bool:
        """Check if user role has permission for required role."""
        user_level = ROLE_HIERARCHY.get(user_role, 999)
        required_level = ROLE_HIERARCHY.get(required_role, 999)
        return user_level <= required_level

    @staticmethod
    def get_role_permissions(role: str) -> List[str]:
        """Get list of permissions for a role."""
        role_level = ROLE_HIERARCHY.get(role, 999)
        permissions = []
        
        for role_name, level in ROLE_HIERARCHY.items():
            if role_level <= level:
                permissions.append(role_name)
        
        return permissions

    @staticmethod
    def validate_role_permissions(permissions: List[str]) -> bool:
        """Validate if all permissions are valid."""
        return all(permission in VALID_PERMISSIONS for permission in permissions)

    @staticmethod
    def get_role_level(role: str) -> int:
        """Get the hierarchy level for a role."""
        return ROLE_HIERARCHY.get(role, 999)

    @staticmethod
    def is_valid_role(role: str) -> bool:
        """Check if a role is valid."""
        return role in ROLE_HIERARCHY

    @staticmethod
    def get_subordinate_roles(role: str) -> List[str]:
        """Get all roles that are subordinate to the given role."""
        role_level = ROLE_HIERARCHY.get(role, 999)
        return [r for r, level in ROLE_HIERARCHY.items() if level > role_level]