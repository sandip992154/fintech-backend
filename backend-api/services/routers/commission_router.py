"""
API Routes for Commission Management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from decimal import Decimal
import io
import json

from database.database import get_db
from services.auth.auth import get_current_user
from services.models.models import User
from services.models.scheme_models import Commission, ServiceOperator, ServiceTypeEnum, Scheme
from services.business.scheme_service import CommissionService, ServiceOperatorService
from services.schemas.scheme_schemas import (
    CommissionCreate, CommissionUpdate, CommissionOut, ServiceOperatorCreate,
    ServiceOperatorOut, BulkCommissionCreate, BulkCommissionResponse,
    CommissionListResponse, StandardResponse, ServiceTypeEnum as ServiceTypeSchema,
    CommissionSlabCreate, CommissionSlabCreateAPI, CommissionSlabOut
)
from config.role_manager import RoleManager
from services.utils.role_hierarchy import RoleHierarchy
from services.models.scheme_models import CommissionSlab


router = APIRouter(tags=["Commission Management"])


def check_commission_permissions(current_user: User, action: str, scheme_id: int = None, db: Session = None):
    """Check if user has permissions for commission operations with scheme ownership validation"""
    from services.business.scheme_service import SchemeService
    
    user_role = current_user.role.name.lower()
    permissions = RoleHierarchy.get_role_permissions(user_role)
    
    # Check basic action permissions
    permission_map = {
        "create": "commissions.create",
        "update": "commissions.update",
        "delete": "commissions.delete",
        "read": True  # All authenticated users can read their accessible commissions
    }
    
    required_permission = permission_map.get(action)
    if required_permission is True:
        return True
        
    if required_permission and not permissions.get(required_permission, False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user_role}' is not authorized to {action} commissions"
        )
    
    # For scheme-specific operations, check scheme access
    if scheme_id and db:
        scheme_service = SchemeService(db)
        scheme = scheme_service.get_scheme_by_id(scheme_id)
        
        if scheme and not scheme.can_be_accessed_by_user(current_user.id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to commissions for this scheme"
            )
    if action == "read":
        return True


@router.post("/schemes/{scheme_id}/commissions", response_model=CommissionOut, status_code=status.HTTP_201_CREATED)
async def create_commission(
    scheme_id: int,
    commission_data: CommissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new commission structure for a scheme.
    
    **Permissions**: SuperAdmin, Admin, Whitelabel (for downstream roles only)
    """
    check_commission_permissions(current_user, "create")
    
    commission_service = CommissionService(db)
    commission = commission_service.create_commission(
        scheme_id, 
        commission_data, 
        user_id=current_user.id,
        user_role=current_user.role
    )
    
    return commission


@router.get("/schemes/{scheme_id}/commissions", response_model=CommissionListResponse)
async def get_scheme_commissions(
    scheme_id: int,
    service: ServiceTypeSchema = Query(..., description="Service type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all commissions for a scheme filtered by service type.
    
    **Permissions**: All authenticated users
    """
    check_commission_permissions(current_user, "read")
    
    commission_service = CommissionService(db)
    commissions = commission_service.get_commissions_by_scheme_and_service(
        scheme_id, service, current_user.id, current_user.role
    )
    
    return CommissionListResponse(
        service=service,
        entries=commissions
    )


@router.post("/schemes/{scheme_id}/commissions/bulk", response_model=BulkCommissionResponse)
async def bulk_create_commissions(
    scheme_id: int,
    bulk_data: BulkCommissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk create/update commissions for a service.
    
    **Permissions**: SuperAdmin, Admin, Whitelabel (with role-based restrictions)
    """
    check_commission_permissions(current_user, "create")
    
    commission_service = CommissionService(db)
    result = commission_service.bulk_create_commissions(
        scheme_id, 
        bulk_data, 
        user_id=current_user.id,
        user_role=current_user.role.name.lower()
    )
    
    return BulkCommissionResponse(**result)


@router.put("/schemes/{scheme_id}/commissions/bulk-update", response_model=BulkCommissionResponse)
async def bulk_update_commissions(
    scheme_id: int,
    bulk_data: BulkCommissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk update existing commissions for a service.
    Only updates existing commissions, does not create new ones.
    
    **Permissions**: SuperAdmin, Admin, Whitelabel (with role-based restrictions)
    """
    check_commission_permissions(current_user, "update")
    
    commission_service = CommissionService(db)
    result = commission_service.bulk_update_commissions(
        scheme_id, 
        bulk_data, 
        user_id=current_user.id,
        user_role=current_user.role.name.lower()
    )
    
    return BulkCommissionResponse(**result)


@router.get("/schemes/{scheme_id}/commissions/export")
async def export_commissions(
    scheme_id: int,
    service: ServiceTypeSchema = Query(..., description="Service type"),
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export commissions for a scheme and service type.
    
    **Permissions**: All authenticated users
    """
    check_commission_permissions(current_user, "read")
    
    commission_service = CommissionService(db)
    
    if format == "csv":
        csv_data = commission_service.export_commissions_csv(scheme_id, service)
        
        response = StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=commissions_{service.value}_{scheme_id}.csv"}
        )
        return response
    
    elif format == "json":
        commissions = commission_service.get_commissions_by_scheme_and_service(
            scheme_id, service
        )
        
        # Convert to JSON format matching the frontend expectations
        json_data = {
            "service": service.value,
            "entries": []
        }
        
        for commission in commissions:
            if service == ServiceTypeEnum.AEPS and commission.slabs:
                entry = {
                    "operator": commission.operator.name,
                    "commission_type": commission.commission_type.value,
                    "slabs": [
                        {
                            "slab_min": slab.slab_min,
                            "slab_max": slab.slab_max,
                            "whitelabel": slab.whitelabel,
                            "md": slab.masterdistributor,
                            "distributor": slab.distributor,
                            "retailer": slab.retailer
                        }
                        for slab in commission.slabs
                    ]
                }
            else:
                entry = {
                    "operator": commission.operator.name,
                    "commission_type": commission.commission_type.value,
                    "whitelabel": commission.whitelabel,
                    "masterdistributor": commission.masterdistributor,
                    "distributor": commission.distributor,
                    "retailer": commission.retailer
                }
            
            json_data["entries"].append(entry)
        
        return Response(
            content=json.dumps(json_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=commissions_{service.value}_{scheme_id}.json"}
        )


@router.post("/schemes/{scheme_id}/commissions/import", response_model=BulkCommissionResponse)
async def import_commissions(
    scheme_id: int,
    bulk_data: BulkCommissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import commissions from CSV/Excel data.
    
    **Permissions**: SuperAdmin, Admin, Whitelabel (with role-based restrictions)
    """
    check_commission_permissions(current_user, "create")
    
    commission_service = CommissionService(db)
    result = commission_service.bulk_create_commissions(
        scheme_id, 
        bulk_data, 
        user_id=current_user.id,
        user_role=current_user.role.name.lower()
    )
    
    return BulkCommissionResponse(**result)


@router.get("/commissions/calculate")
async def calculate_commission(
    scheme_id: int = Query(..., description="Scheme ID"),
    operator_id: int = Query(..., description="Operator ID"),
    service_type: ServiceTypeSchema = Query(..., description="Service type"),
    amount: Decimal = Query(..., gt=0, description="Transaction amount"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate commission for a specific user, operator, and amount.
    
    **Permissions**: All authenticated users (for their own role)
    """
    check_commission_permissions(current_user, "read")
    
    commission_service = CommissionService(db)
    user_role = current_user.role.name.lower()
    
    result = commission_service.calculate_commission_for_user(
        scheme_id=scheme_id,
        operator_id=operator_id,
        service_type=service_type,
        user_role=user_role,
        amount=amount
    )
    
    return result


@router.put("/commissions/{commission_id}", response_model=CommissionOut)
async def update_commission(
    commission_id: int,
    commission_data: CommissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing commission structure.
    
    **Permissions**: SuperAdmin, Admin, Whitelabel (with role-based field restrictions)
    """
    check_commission_permissions(current_user, "update")
    
    # Get existing commission and its scheme
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission not found"
        )
    
    # Check scheme access through ownership
    scheme = db.query(Scheme).filter(Scheme.id == commission.scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated scheme not found"
        )
    
    # Check if user can access this scheme
    if not RoleHierarchy.can_user_access_scheme(current_user, scheme):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this scheme"
        )
    
    # Get editable fields based on user role
    user_role = current_user.role.name.lower()
    editable_fields = RoleHierarchy.get_editable_commission_fields(user_role)
    
    # Filter update data to only include editable fields
    update_data = commission_data.model_dump(exclude_unset=True) if hasattr(commission_data, 'model_dump') else commission_data.dict(exclude_unset=True)
    filtered_update_data = {
        field: value for field, value in update_data.items()
        if field in editable_fields
    }
    
    if not filtered_update_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your role ({user_role}) cannot edit any commission fields"
        )
    
    # Apply updates
    for field, value in filtered_update_data.items():
        setattr(commission, field, value)
    
    db.commit()
    db.refresh(commission)
    
    return commission


@router.delete("/commissions/{commission_id}", response_model=StandardResponse)
async def delete_commission(
    commission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) a commission structure.
    
    **Permissions**: SuperAdmin, Admin only
    """
    check_commission_permissions(current_user, "delete")
    
    # Get existing commission and its scheme
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission not found"
        )
    
    # Check scheme access through ownership
    scheme = db.query(Scheme).filter(Scheme.id == commission.scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated scheme not found"
        )
    
    # Check if user can access this scheme
    if not RoleHierarchy.can_user_access_scheme(current_user, scheme):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this scheme"
        )
    
    # Soft delete by deactivating
    commission.is_active = False
    db.commit()
    
    return StandardResponse(
        success=True,
        message="Commission deleted successfully"
    )


# Service Operator endpoints
@router.post("/operators", response_model=ServiceOperatorOut, status_code=status.HTTP_201_CREATED)
async def create_service_operator(
    operator_data: ServiceOperatorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new service operator.
    
    **Permissions**: SuperAdmin, Admin only
    """
    user_role = current_user.role.name.lower()
    if user_role not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperAdmin and Admin can create operators"
        )
    
    operator_service = ServiceOperatorService(db)
    operator = operator_service.create_operator(operator_data)
    
    return ServiceOperatorOut.from_orm(operator)


@router.get("/operators", response_model=List[ServiceOperatorOut])
async def list_service_operators(
    service_type: Optional[ServiceTypeSchema] = Query(None, description="Filter by service type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of service operators.
    
    **Permissions**: All authenticated users
    """
    check_commission_permissions(current_user, "read")
    
    operator_service = ServiceOperatorService(db)
    
    if service_type:
        operators = operator_service.get_operators_by_service(service_type)
    else:
        operators = db.query(ServiceOperator).filter(
            ServiceOperator.is_active == True
        ).all()
    
    # Convert to Pydantic models
    return [ServiceOperatorOut.from_orm(operator) for operator in operators]


# ==================== COMMISSION SLAB ENDPOINTS ====================

@router.get("/commissions/{commission_id}/slabs", response_model=List[CommissionSlabOut])
async def get_commission_slabs(
    commission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all slabs for a commission.
    
    **Permissions**: All authenticated users (for their accessible commissions)
    """
    check_commission_permissions(current_user, "read")
    
    commission_service = CommissionService(db)
    
    # Verify user can access this commission
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission not found"
        )
    
    # Check scheme access through ownership
    scheme = db.query(Scheme).filter(Scheme.id == commission.scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated scheme not found"
        )
    
    # Check if user can access this scheme
    if not RoleHierarchy.can_user_access_scheme(current_user, scheme):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this commission"
        )
    
    slabs = commission_service.get_commission_slabs(commission_id)
    return [CommissionSlabOut.from_orm(slab) for slab in slabs]


@router.post("/commission-slabs", response_model=CommissionSlabOut, status_code=status.HTTP_201_CREATED)
async def create_commission_slab(
    slab_data: CommissionSlabCreateAPI,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new commission slab.
    
    **Permissions**: SuperAdmin, Admin, Whitelabel (with role-based field restrictions)
    """
    check_commission_permissions(current_user, "create")
    
    commission_service = CommissionService(db)
    commission_id = slab_data.commission_id
    
    # Verify user can access this commission
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission not found"
        )
    
    # Check scheme access through ownership
    scheme = db.query(Scheme).filter(Scheme.id == commission.scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated scheme not found"
        )
    
    # Check if user can access this scheme
    if not RoleHierarchy.can_user_access_scheme(current_user, scheme):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this commission"
        )
    
    # Get editable fields based on user role
    user_role = current_user.role.name.lower()
    
    # Add debug logging
    print(f"DEBUG: User role: {user_role}")
    print(f"DEBUG: User role type: {type(current_user.role.name)}")
    
    editable_fields = RoleHierarchy.get_editable_commission_fields(user_role)
    print(f"DEBUG: Editable fields: {editable_fields}")
    
    # Filter slab data to only include editable fields
    slab_dict = slab_data.model_dump(exclude={'commission_id'}) if hasattr(slab_data, 'model_dump') else slab_data.dict(exclude={'commission_id'})  # Exclude commission_id from validation
    print(f"DEBUG: Original slab data: {slab_dict}")
    
    filtered_slab_dict = {
        field: value for field, value in slab_dict.items()
        if field in editable_fields or field in ['slab_min', 'slab_max']  # Always allow range fields
    }
    print(f"DEBUG: Filtered slab data: {filtered_slab_dict}")
    
    # Check if user can edit any commission fields
    commission_fields = ['superadmin', 'admin', 'whitelabel', 'masterdistributor', 'distributor', 'retailer', 'customer']
    editable_commission_fields = [field for field in commission_fields if field in editable_fields]
    print(f"DEBUG: Editable commission fields: {editable_commission_fields}")
    
    if not editable_commission_fields:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your role ({user_role}) cannot edit any commission fields. Available fields: {editable_fields}"
        )
    
    # Create filtered slab data object
    filtered_slab_data = CommissionSlabCreate(**filtered_slab_dict)
    
    slab = commission_service.create_commission_slab(commission_id, filtered_slab_data)
    return CommissionSlabOut.from_orm(slab)


@router.put("/commission-slabs/{slab_id}", response_model=CommissionSlabOut)
async def update_commission_slab(
    slab_id: int,
    slab_data: CommissionSlabCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing commission slab.
    
    **Permissions**: SuperAdmin, Admin, Whitelabel (with role-based field restrictions)
    """
    check_commission_permissions(current_user, "update")
    
    commission_service = CommissionService(db)
    
    # Get existing slab
    db_slab = db.query(CommissionSlab).filter(CommissionSlab.id == slab_id).first()
    if not db_slab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission slab not found"
        )
    
    # Get associated commission and scheme
    commission = db.query(Commission).filter(Commission.id == db_slab.commission_id).first()
    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated commission not found"
        )
    
    scheme = db.query(Scheme).filter(Scheme.id == commission.scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated scheme not found"
        )
    
    # Check if user can access this scheme
    if not RoleHierarchy.can_user_access_scheme(current_user, scheme):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this commission slab"
        )
    
    # Get editable fields based on user role
    user_role = current_user.role.name.lower()
    editable_fields = RoleHierarchy.get_editable_commission_fields(user_role)
    
    # Filter update data to only include editable fields
    update_dict = slab_data.model_dump(exclude_unset=True) if hasattr(slab_data, 'model_dump') else slab_data.dict(exclude_unset=True)
    filtered_update_dict = {
        field: value for field, value in update_dict.items()
        if field in editable_fields or field in ['slab_min', 'slab_max']  # Always allow range fields
    }
    
    if not filtered_update_dict:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your role ({user_role}) cannot edit any slab fields"
        )
    
    # Create filtered update data object
    filtered_slab_data = CommissionSlabCreate(**filtered_update_dict)
    
    slab = commission_service.update_commission_slab(slab_id, filtered_slab_data)
    return CommissionSlabOut.from_orm(slab)


@router.delete("/commission-slabs/{slab_id}", response_model=StandardResponse)
async def delete_commission_slab(
    slab_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) a commission slab.
    
    **Permissions**: SuperAdmin, Admin only
    """
    check_commission_permissions(current_user, "delete")
    
    commission_service = CommissionService(db)
    
    # Get existing slab
    db_slab = db.query(CommissionSlab).filter(CommissionSlab.id == slab_id).first()
    if not db_slab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission slab not found"
        )
    
    # Get associated commission and scheme
    commission = db.query(Commission).filter(Commission.id == db_slab.commission_id).first()
    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated commission not found"
        )
    
    scheme = db.query(Scheme).filter(Scheme.id == commission.scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated scheme not found"
        )
    
    # Check if user can access this scheme
    if not RoleHierarchy.can_user_access_scheme(current_user, scheme):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this commission slab"
        )
    
    commission_service.delete_commission_slab(slab_id)
    
    return StandardResponse(
        success=True,
        message="Commission slab deleted successfully"
    )