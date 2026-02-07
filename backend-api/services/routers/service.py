from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List
import logging

from database.database import get_db
from services.models.transaction_models import ServiceCategory, ServiceProvider
from services.schemas.transaction_schemas import (
    ServiceCategoryCreate,
    ServiceCategoryUpdate,
    ServiceCategoryOut,
    ServiceProviderCreate,
    ServiceProviderUpdate,
    ServiceProviderOut
)
from utils.error_handlers import APIErrorResponse, handle_database_exceptions, validate_required_fields, validate_user_permissions

router = APIRouter(prefix="/services", tags=["Service Management"])
logger = logging.getLogger(__name__)

# Service Category Routes
@router.post("/categories/create", response_model=ServiceCategoryOut)
async def create_service_category(
    category: ServiceCategoryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new service category with comprehensive validation and error handling.
    """
    logger.info(f"Creating service category: {category.name}")
    
    try:
        # Validate required fields
        if not category.name or category.name.strip() == "":
            raise APIErrorResponse.validation_error(
                message="Service category name is required",
                details={
                    "missing_field": "name",
                    "action": "provide_valid_category_name"
                },
                field="name"
            )

        # Check for duplicate category name
        existing_category = db.query(ServiceCategory).filter(
            ServiceCategory.name.ilike(category.name.strip())
        ).first()
        
        if existing_category:
            raise APIErrorResponse.conflict_error(
                message="Service category with this name already exists",
                details={
                    "existing_name": existing_category.name,
                    "provided_name": category.name,
                    "action": "use_different_category_name"
                },
                conflicting_field="name"
            )

        # Create new category
        category_data = category.model_dump()
        category_data['name'] = category_data['name'].strip()
        
        db_category = ServiceCategory(**category_data)
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
        logger.info(f"Service category created successfully: {db_category.name} (ID: {db_category.id})")
        return db_category

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error creating service category: {str(e)}")
        raise APIErrorResponse.conflict_error(
            message="Service category creation failed due to data conflict",
            details={
                "error": "database_constraint_violation",
                "category_name": category.name,
                "action": "check_for_duplicate_names_or_constraints"
            }
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating service category: {str(e)}")
        raise APIErrorResponse.database_error(
            message="Failed to create service category",
            details={
                "error": "database_transaction_failed",
                "category_name": category.name,
                "action": "try_again_or_contact_administrator"
            }
        )
    except HTTPException:
        # Re-raise APIErrorResponse exceptions
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating service category: {str(e)}")
        raise APIErrorResponse.database_error(
            message="An unexpected error occurred while creating service category",
            details={
                "error": "unexpected_creation_error",
                "category_name": category.name,
                "action": "contact_administrator"
            }
        )

@router.get("/categories", response_model=List[ServiceCategoryOut])
async def get_service_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get service categories with pagination and comprehensive error handling.
    """
    logger.info(f"Fetching service categories - skip: {skip}, limit: {limit}")
    
    try:
        # Validate pagination parameters
        if skip < 0:
            raise APIErrorResponse.validation_error(
                message="Skip parameter cannot be negative",
                details={
                    "provided_skip": skip,
                    "minimum_skip": 0,
                    "action": "provide_non_negative_skip_value"
                },
                field="skip"
            )

        if limit <= 0 or limit > 1000:
            raise APIErrorResponse.validation_error(
                message="Limit parameter must be between 1 and 1000",
                details={
                    "provided_limit": limit,
                    "minimum_limit": 1,
                    "maximum_limit": 1000,
                    "action": "provide_valid_limit_value"
                },
                field="limit"
            )

        categories = db.query(ServiceCategory)\
            .filter(ServiceCategory.is_active == True)\
            .offset(skip)\
            .limit(limit)\
            .all()
            
        logger.info(f"Retrieved {len(categories)} service categories")
        return categories

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving service categories: {str(e)}")
        raise APIErrorResponse.database_error(
            message="Failed to retrieve service categories",
            details={
                "error": "database_query_failed",
                "pagination": {"skip": skip, "limit": limit},
                "action": "try_again_or_contact_administrator"
            }
        )
    except HTTPException:
        # Re-raise APIErrorResponse exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving service categories: {str(e)}")
        raise APIErrorResponse.database_error(
            message="An unexpected error occurred while retrieving service categories",
            details={
                "error": "unexpected_retrieval_error",
                "pagination": {"skip": skip, "limit": limit},
                "action": "contact_administrator"
            }
        )

@router.put("/categories/{category_id}", response_model=ServiceCategoryOut)
async def update_service_category(
    category_id: int,
    category: ServiceCategoryUpdate,
    db: Session = Depends(get_db)
):
    db_category = db.query(ServiceCategory).filter(
        ServiceCategory.id == category_id
    ).first()
    
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service category not found"
        )
    
    for key, value in category.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}")
async def delete_service_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    db_category = db.query(ServiceCategory).filter(
        ServiceCategory.id == category_id
    ).first()
    
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service category not found"
        )
    
    db_category.is_active = False
    db.commit()
    return {"message": "Service category deactivated successfully"}

# Service Provider Routes
@router.post("/providers/create", response_model=ServiceProviderOut)
async def create_service_provider(
    provider: ServiceProviderCreate,
    db: Session = Depends(get_db)
):
    # Verify category exists
    category = db.query(ServiceCategory).filter(
        ServiceCategory.id == provider.category_id,
        ServiceCategory.is_active == True
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service category not found or inactive"
        )
    
    db_provider = ServiceProvider(**provider.model_dump())
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider

@router.get("/providers", response_model=List[ServiceProviderOut])
async def get_service_providers(
    category_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(ServiceProvider).filter(ServiceProvider.is_active == True)
    
    if category_id:
        query = query.filter(ServiceProvider.category_id == category_id)
    
    providers = query.offset(skip).limit(limit).all()
    return providers

@router.put("/providers/{provider_id}", response_model=ServiceProviderOut)
async def update_service_provider(
    provider_id: int,
    provider: ServiceProviderUpdate,
    db: Session = Depends(get_db)
):
    db_provider = db.query(ServiceProvider).filter(
        ServiceProvider.id == provider_id
    ).first()
    
    if not db_provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service provider not found"
        )
    
    for key, value in provider.model_dump(exclude_unset=True).items():
        setattr(db_provider, key, value)
    
    db.commit()
    db.refresh(db_provider)
    return db_provider

@router.delete("/providers/{provider_id}")
async def delete_service_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    db_provider = db.query(ServiceProvider).filter(
        ServiceProvider.id == provider_id
    ).first()
    
    if not db_provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service provider not found"
        )
    
    db_provider.is_active = False
    db.commit()
    return {"message": "Service provider deactivated successfully"}
