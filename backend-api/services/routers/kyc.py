from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.database import get_db
from services.models.models import User
from services.models.user_models import KYCDocument, KYCStatus
from services.schemas.kyc_schemas import (
    KYCCreate, KYCResponse, KYCStatusCheck, KYCVerifyRequest
)
from services.auth.auth import get_current_user
from services.utils.document_handler import process_profile_photo, save_document, delete_document
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import and_
import logging
import traceback

# Configure logger
logger = logging.getLogger("bandaru_api")

router = APIRouter(prefix="/kyc", tags=["KYC"])

# Standardized error response structure
class KYCErrorResponse:
    @staticmethod
    def create_error_response(
        error_code: str,
        message: str,
        details: Optional[str] = None,
        status_code: int = 500,
        field_errors: Optional[Dict[str, str]] = None
    ) -> HTTPException:
        """Create a standardized error response for KYC operations"""
        error_data = {
            "error": True,
            "error_code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "KYC"
        }
        
        if details:
            error_data["details"] = details
        
        if field_errors:
            error_data["field_errors"] = field_errors
            
        return HTTPException(status_code=status_code, detail=error_data)

    @staticmethod
    def database_error(operation: str, details: str = None) -> HTTPException:
        """Standardized database error response"""
        return KYCErrorResponse.create_error_response(
            error_code="DATABASE_ERROR",
            message=f"Database operation failed during {operation}",
            details=details or "Please try again later or contact support if the issue persists",
            status_code=500
        )

    @staticmethod
    def validation_error(field: str, message: str) -> HTTPException:
        """Standardized validation error response"""
        return KYCErrorResponse.create_error_response(
            error_code="VALIDATION_ERROR",
            message="Input validation failed",
            details=f"Invalid {field}: {message}",
            status_code=400,
            field_errors={field: message}
        )

    @staticmethod
    def not_found_error(resource: str, identifier: str = None) -> HTTPException:
        """Standardized not found error response"""
        details = f"{resource} not found"
        if identifier:
            details += f" for identifier: {identifier}"
        
        return KYCErrorResponse.create_error_response(
            error_code="NOT_FOUND",
            message=details,
            details="Please verify the request parameters and try again",
            status_code=404
        )

    @staticmethod
    def unauthorized_error(operation: str) -> HTTPException:
        """Standardized unauthorized error response"""
        return KYCErrorResponse.create_error_response(
            error_code="UNAUTHORIZED",
            message=f"Unauthorized to perform {operation}",
            details="Please ensure you are logged in and have the required permissions",
            status_code=401
        )

    @staticmethod
    def forbidden_error(operation: str, required_role: str = None) -> HTTPException:
        """Standardized forbidden error response"""
        details = f"Insufficient permissions to {operation}"
        if required_role:
            details += f". Required role: {required_role}"
        
        return KYCErrorResponse.create_error_response(
            error_code="FORBIDDEN",
            message="Access forbidden",
            details=details,
            status_code=403
        )

    @staticmethod
    def file_error(operation: str, details: str) -> HTTPException:
        """Standardized file operation error response"""
        return KYCErrorResponse.create_error_response(
            error_code="FILE_ERROR",
            message=f"File {operation} failed",
            details=details,
            status_code=400
        )

    @staticmethod  
    def business_rule_error(rule: str, details: str) -> HTTPException:
        """Standardized business rule violation error response"""
        return KYCErrorResponse.create_error_response(
            error_code="BUSINESS_RULE_VIOLATION",
            message=f"Business rule violation: {rule}",
            details=details,
            status_code=409
        )

@router.get("/health")
async def kyc_health_check():
    """
    Simple health check endpoint for KYC service (no authentication required)
    """
    return {"status": "healthy", "service": "kyc", "timestamp": datetime.utcnow()}

@router.get("/status/test")
async def test_kyc_status():
    """
    Test endpoint for KYC status without authentication (for development only)
    """
    return {
        "status": "not_submitted",
        "message": "Test KYC status - no authentication required",
        "test": True
    }

@router.post("/upload/profile-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload profile photo for KYC. Photo will be resized to passport size (60px X 80px).
    """
    try:
        # Validate file
        if not file:
            raise KYCErrorResponse.validation_error("file", "Profile photo is required")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise KYCErrorResponse.validation_error(
                "file_type", 
                f"Invalid file type '{file.content_type}'. Only image files are allowed"
            )
        
        # Validate file size (limit to 5MB)
        if file.size and file.size > 5 * 1024 * 1024:
            raise KYCErrorResponse.validation_error(
                "file_size", 
                f"File size {file.size} bytes exceeds maximum allowed size of 5MB"
            )
        
        logger.info(f"Processing profile photo upload for user {current_user.id}")
        
        # Process and save photo
        photo_url = await process_profile_photo(file)
        
        if not photo_url:
            raise KYCErrorResponse.file_error(
                "processing", 
                "Failed to process the uploaded image. Please try with a different image"
            )
        
        # Update KYC document if exists
        try:
            kyc = db.query(KYCDocument).filter(
                KYCDocument.user_id == current_user.id
            ).first()
            
            if kyc:
                # Store old photo URL for cleanup
                old_photo_url = kyc.profile_photo_url
                
                # Update with new photo
                kyc.profile_photo_url = photo_url
                db.commit()
                
                # Delete old photo if exists (after successful database update)
                if old_photo_url:
                    try:
                        await delete_document(old_photo_url)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to delete old profile photo: {cleanup_error}")
                
                logger.info(f"Profile photo updated successfully for user {current_user.id}")
            else:
                logger.info(f"Profile photo uploaded but no KYC record found for user {current_user.id}")
            
        except SQLAlchemyError as db_error:
            logger.error(f"Database error during profile photo update: {db_error}")
            # Try to clean up uploaded file
            try:
                await delete_document(photo_url)
            except:
                pass
            raise KYCErrorResponse.database_error(
                "profile photo update",
                "Failed to save profile photo information to database"
            )
        
        return {
            "success": True,
            "url": photo_url, 
            "message": "Profile photo uploaded and processed successfully",
            "data": {
                "photo_url": photo_url,
                "user_id": current_user.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during profile photo upload: {e}\n{traceback.format_exc()}")
        raise KYCErrorResponse.create_error_response(
            error_code="UPLOAD_ERROR",
            message="Failed to upload profile photo",
            details="An unexpected error occurred. Please try again or contact support",
            status_code=500
        )

@router.post("/upload/{doc_type}")
async def upload_document(
    doc_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload KYC document. Supported document types:
    - pan_card: PAN Card document
    - company_pan: Company PAN Card document  
    - aadhar_card: Aadhar Card document
    - address_proof: Address proof document
    """
    valid_doc_types = {
        "pan_card": "pan_card_url",
        "company_pan": "company_pan_card_url",
        "aadhar_card": "aadhar_card_url", 
        "address_proof": "address_proof_url"
    }
    
    try:
        # Validate document type
        if doc_type not in valid_doc_types:
            raise KYCErrorResponse.validation_error(
                "doc_type",
                f"Invalid document type '{doc_type}'. Must be one of: {', '.join(valid_doc_types.keys())}"
            )
        
        # Validate file
        if not file:
            raise KYCErrorResponse.validation_error("file", f"{doc_type} document is required")
        
        # Validate file type (allow images and PDFs)
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
        if not file.content_type or file.content_type not in allowed_types:
            raise KYCErrorResponse.validation_error(
                "file_type",
                f"Invalid file type '{file.content_type}'. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Validate file size (limit to 10MB for documents)
        if file.size and file.size > 10 * 1024 * 1024:
            raise KYCErrorResponse.validation_error(
                "file_size",
                f"File size {file.size} bytes exceeds maximum allowed size of 10MB"
            )
        
        logger.info(f"Processing {doc_type} document upload for user {current_user.id}")
        
        # Save document
        doc_url = await save_document(file, doc_type, current_user.user_code)
        
        if not doc_url:
            raise KYCErrorResponse.file_error(
                "processing",
                "Failed to process the uploaded document. Please try with a different file"
            )
        
        # Update KYC document if exists
        try:
            kyc = db.query(KYCDocument).filter(
                KYCDocument.user_id == current_user.id
            ).first()
            
            if kyc:
                # Store old document URL for cleanup
                field_name = valid_doc_types[doc_type]
                old_url = getattr(kyc, field_name, None)
                
                # Update with new document
                setattr(kyc, field_name, doc_url)
                db.commit()
                
                # Delete old document if exists (after successful database update)
                if old_url:
                    try:
                        await delete_document(old_url)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to delete old {doc_type} document: {cleanup_error}")
                
                logger.info(f"{doc_type} document updated successfully for user {current_user.id}")
            else:
                logger.info(f"{doc_type} document uploaded but no KYC record found for user {current_user.id}")
            
        except SQLAlchemyError as db_error:
            logger.error(f"Database error during {doc_type} document update: {db_error}")
            # Try to clean up uploaded file
            try:
                await delete_document(doc_url)
            except:
                pass
            raise KYCErrorResponse.database_error(
                f"{doc_type} document update",
                "Failed to save document information to database"
            )
        
        return {
            "success": True,
            "url": doc_url,
            "message": f"{doc_type.replace('_', ' ').title()} uploaded and processed successfully",
            "data": {
                "document_type": doc_type,
                "document_url": doc_url,
                "user_id": current_user.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {doc_type} document upload: {e}\n{traceback.format_exc()}")
        raise KYCErrorResponse.create_error_response(
            error_code="DOCUMENT_UPLOAD_ERROR",
            message=f"Failed to upload {doc_type} document",
            details="An unexpected error occurred. Please try again or contact support",
            status_code=500
        )

@router.post("/submit", response_model=KYCResponse)
async def submit_kyc(
    payload: KYCCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit KYC documents for verification.
    """
    logger.info(f"KYC submission request by user {current_user.id}")
    
    try:
        # Validate user authentication
        if not current_user or not current_user.id:
            return KYCErrorResponse.unauthorized_error(
                message="User authentication required",
                details={
                    "action": "login_required_to_submit_kyc"
                }
            )

        # Validate payload data
        if not payload:
            return KYCErrorResponse.validation_error(
                message="KYC data is required for submission",
                details={
                    "missing_field": "kyc_payload",
                    "action": "provide_complete_kyc_information"
                }
            )

        # Check for existing KYC
        existing_kyc = db.query(KYCDocument).filter(
            KYCDocument.user_id == current_user.id
        ).first()

        if existing_kyc:
            # Check if existing KYC can be updated
            if existing_kyc.status == KYCStatus.CONFIRMED:
                return KYCErrorResponse.business_rule_error(
                    message="KYC is already confirmed and cannot be modified",
                    details={
                        "current_status": existing_kyc.status,
                        "action": "kyc_already_approved_no_changes_allowed"
                    }
                )
            
            # Update existing KYC
            logger.info(f"Updating existing KYC for user {current_user.id}")
            for key, value in payload.dict().items():
                if value is not None:  # Only update non-null values
                    setattr(existing_kyc, key, value)
            existing_kyc.status = KYCStatus.PENDING
            existing_kyc.submitted_at = datetime.utcnow()
            existing_kyc.verified_at = None
            existing_kyc.rejection_reason = None
        else:
            # Create new KYC
            logger.info(f"Creating new KYC for user {current_user.id}")
            kyc_data = payload.dict()
            kyc_data["user_id"] = current_user.id
            kyc_data["user_code"] = current_user.user_code  # Keep for compatibility
            existing_kyc = KYCDocument(**kyc_data)
            db.add(existing_kyc)

        # Save to database
        db.commit()
        db.refresh(existing_kyc)
        logger.info(f"KYC successfully submitted for user {current_user.id}")

        return existing_kyc
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during KYC submission: {str(e)}")
        return KYCErrorResponse.database_error(
            message="Failed to submit KYC documents",
            details={
                "error": "database_transaction_failed",
                "action": "try_again_or_contact_support"
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during KYC submission: {str(e)}")
        return KYCErrorResponse.database_error(
            message="An unexpected error occurred during KYC submission",
            details={
                "error": "unexpected_submission_error",
                "action": "contact_support"
            }
        )

@router.post("/submit-form")
async def submit_kyc_form(
    # Required fields
    aadhar_number: str = Form(..., description="Aadhar card number (required)"),
    pan_number: str = Form(..., description="PAN card number (required)"),
    
    # Personal Information
    full_name: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    
    # Contact Information
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    pin_code: Optional[str] = Form(None),
    
    # Business Information
    business_name: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    business_address: Optional[str] = Form(None),
    company_pan_number: Optional[str] = Form(None),
    
    # Bank Details
    bank_name: Optional[str] = Form(None),
    account_number: Optional[str] = Form(None),
    ifsc_code: Optional[str] = Form(None),
    account_holder_name: Optional[str] = Form(None),
    branch_name: Optional[str] = Form(None),
    
    # Document Files
    aadhar_card: Optional[UploadFile] = File(None),
    pan_card: Optional[UploadFile] = File(None),
    company_pan_card: Optional[UploadFile] = File(None),
    photo: Optional[UploadFile] = File(None),
    signature: Optional[UploadFile] = File(None),
    business_license: Optional[UploadFile] = File(None),
    gst_certificate: Optional[UploadFile] = File(None),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit KYC form with file uploads using multipart/form-data.
    Now stores all KYC data in the expanded database schema.
    """
    try:
        # Validate required fields
        if not aadhar_number or len(aadhar_number.strip()) < 12:
            raise HTTPException(
                status_code=400,
                detail="Valid Aadhar number is required (12 digits)"
            )
        
        if not pan_number or len(pan_number.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Valid PAN number is required (10 characters)"
            )
        
        # Process document files
        document_urls = {}
        file_mappings = {
            'photo': photo,
            'aadhar_card': aadhar_card,
            'pan_card': pan_card,
            'company_pan_card': company_pan_card,
            'signature': signature,
            'business_license': business_license,
            'gst_certificate': gst_certificate
        }
        
        # Mapping from form field names to database column names
        field_name_mapping = {
            'photo': 'profile_photo_url',
            'aadhar_card': 'aadhar_card_url',
            'pan_card': 'pan_card_url',
            'company_pan_card': 'company_pan_card_url',
            'signature': 'signature_url',
            'business_license': 'business_license_url',
            'gst_certificate': 'gst_certificate_url'
        }
        
        for doc_type, file in file_mappings.items():
            if file and file.filename:
                try:
                    db_field_name = field_name_mapping.get(doc_type, f"{doc_type}_url")
                    document_urls[db_field_name] = await save_document(file, doc_type, current_user.id)
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error uploading {doc_type}: {str(e)}"
                    )
        
        # Check for existing KYC
        existing_kyc = db.query(KYCDocument).filter(
            KYCDocument.user_id == current_user.id
        ).first()

        if existing_kyc:
            # Update existing KYC with all fields
            existing_kyc.pan_card_no = pan_number.strip()
            existing_kyc.aadhar_card_no = aadhar_number.strip()
            existing_kyc.status = KYCStatus.PENDING
            existing_kyc.submitted_at = datetime.utcnow()
            existing_kyc.verified_at = None
            existing_kyc.rejection_reason = None
            
            # Update personal information
            if full_name: existing_kyc.full_name = full_name.strip()
            if date_of_birth: existing_kyc.date_of_birth = date_of_birth.strip()
            if gender: existing_kyc.gender = gender.strip()
            
            # Update contact information
            if email: existing_kyc.email = email.strip()
            if phone: existing_kyc.phone = phone.strip()
            if address: existing_kyc.address = address.strip()
            if city: existing_kyc.city = city.strip()
            if state: existing_kyc.state = state.strip()
            if pin_code: existing_kyc.pin_code = pin_code.strip()
            
            # Update business information
            if business_name: existing_kyc.business_name = business_name.strip()
            if business_type: existing_kyc.business_type = business_type.strip()
            if business_address: existing_kyc.business_address = business_address.strip()
            if company_pan_number: existing_kyc.company_pan_number = company_pan_number.strip()
            
            # Update bank details
            if bank_name: existing_kyc.bank_name = bank_name.strip()
            if account_number: existing_kyc.account_number = account_number.strip()
            if ifsc_code: existing_kyc.ifsc_code = ifsc_code.strip()
            if account_holder_name: existing_kyc.account_holder_name = account_holder_name.strip()
            if branch_name: existing_kyc.branch_name = branch_name.strip()
            
            # Update document URLs
            for url_field, url_value in document_urls.items():
                setattr(existing_kyc, url_field, url_value)
                
        else:
            # Create new KYC with all fields
            new_kyc_data = {
                "user_id": current_user.id,
                "pan_card_no": pan_number.strip(),
                "aadhar_card_no": aadhar_number.strip(),
                "status": KYCStatus.PENDING,
                "submitted_at": datetime.utcnow(),
                
                # Personal Information
                "full_name": full_name.strip() if full_name else None,
                "date_of_birth": date_of_birth.strip() if date_of_birth else None,
                "gender": gender.strip() if gender else None,
                
                # Contact Information
                "email": email.strip() if email else None,
                "phone": phone.strip() if phone else None,
                "address": address.strip() if address else None,
                "city": city.strip() if city else None,
                "state": state.strip() if state else None,
                "pin_code": pin_code.strip() if pin_code else None,
                
                # Business Information
                "business_name": business_name.strip() if business_name else None,
                "business_type": business_type.strip() if business_type else None,
                "business_address": business_address.strip() if business_address else None,
                "company_pan_number": company_pan_number.strip() if company_pan_number else None,
                
                # Bank Details
                "bank_name": bank_name.strip() if bank_name else None,
                "account_number": account_number.strip() if account_number else None,
                "ifsc_code": ifsc_code.strip() if ifsc_code else None,
                "account_holder_name": account_holder_name.strip() if account_holder_name else None,
                "branch_name": branch_name.strip() if branch_name else None,
            }
            
            # Add document URLs
            new_kyc_data.update(document_urls)
            
            existing_kyc = KYCDocument(**new_kyc_data)
            db.add(existing_kyc)

        db.commit()
        db.refresh(existing_kyc)
        
        return {
            "id": existing_kyc.id,
            "user_id": existing_kyc.user_id,
            
            # Personal Information
            "full_name": existing_kyc.full_name,
            "date_of_birth": existing_kyc.date_of_birth,
            "gender": existing_kyc.gender,
            
            # Contact Information
            "email": existing_kyc.email,
            "phone": existing_kyc.phone,
            "address": existing_kyc.address,
            "city": existing_kyc.city,
            "state": existing_kyc.state,
            "pin_code": existing_kyc.pin_code,
            
            # Business Information
            "business_name": existing_kyc.business_name,
            "business_type": existing_kyc.business_type,
            "business_address": existing_kyc.business_address,
            "company_pan_number": existing_kyc.company_pan_number,
            
            # Bank Details
            "bank_name": existing_kyc.bank_name,
            "account_number": existing_kyc.account_number,
            "ifsc_code": existing_kyc.ifsc_code,
            "account_holder_name": existing_kyc.account_holder_name,
            "branch_name": existing_kyc.branch_name,
            
            # Document Information
            "pan_card_no": existing_kyc.pan_card_no,
            "aadhar_card_no": existing_kyc.aadhar_card_no,
            
            # Document URLs
            "profile_photo_url": existing_kyc.profile_photo_url,
            "aadhar_card_url": existing_kyc.aadhar_card_url,
            "pan_card_url": existing_kyc.pan_card_url,
            "company_pan_card_url": existing_kyc.company_pan_card_url,
            "signature_url": existing_kyc.signature_url,
            "business_license_url": existing_kyc.business_license_url,
            "gst_certificate_url": existing_kyc.gst_certificate_url,
            
            # Status and Timestamps
            "status": existing_kyc.status,
            "submitted_at": existing_kyc.submitted_at,
            "verified_at": existing_kyc.verified_at,
            "rejection_reason": existing_kyc.rejection_reason,
            "message": "KYC submitted successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # Log the actual error for debugging
        print(f"KYC Submission Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit KYC application. Please check your data and try again. Error: {str(e)}"
        )

@router.get("/status")
async def check_kyc_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check KYC status for the current user.
    Returns comprehensive status information including progress indicators.
    """
    try:
        logger.info(f"Checking KYC status for user {current_user.id}")
        
        kyc = db.query(KYCDocument).filter(
            KYCDocument.user_id == current_user.id
        ).first()

        if not kyc:
            return {
                "success": True,
                "status": KYCStatus.NOT_SUBMITTED,
                "message": "KYC application not submitted yet",
                "kyc_data": None,
                "progress": {
                    "percentage": 0,
                    "steps_completed": 0,
                    "total_steps": 5,
                    "next_step": "Submit basic information and documents"
                }
            }

        # Define status messages with actionable information
        status_messages = {
            KYCStatus.PENDING: {
                "message": "Your KYC application is under review",
                "details": "Our team is verifying your submitted documents. You will be notified once the review is complete.",
                "action": "Please wait for review completion"
            },
            KYCStatus.CONFIRMED: {
                "message": "Your KYC has been approved successfully", 
                "details": "Your account is now fully verified and all services are available.",
                "action": "You can now access all platform features"
            },
            KYCStatus.REJECTED: {
                "message": "Your KYC application was rejected",
                "details": f"Reason: {kyc.rejection_reason or 'No specific reason provided'}",
                "action": "Please review the rejection reason and resubmit with correct information"
            },
            KYCStatus.HOLD: {
                "message": "Your KYC application is on hold",
                "details": "Additional verification or documents may be required.",
                "action": "Please contact support for more information"
            }
        }

        current_status = status_messages.get(kyc.status, {
            "message": f"Unknown KYC status: {kyc.status}",
            "details": "Please contact support for assistance",
            "action": "Contact customer support"
        })

        # Calculate completion percentage
        required_fields = ['full_name', 'pan_card_no', 'aadhar_card_no', 'profile_photo_url']
        completed_fields = sum(1 for field in required_fields if getattr(kyc, field, None))
        completion_percentage = (completed_fields / len(required_fields)) * 100

        return {
            "success": True,
            "status": kyc.status,
            "message": current_status["message"],
            "details": current_status["details"],
            "recommended_action": current_status["action"],
            "progress": {
                "percentage": completion_percentage,
                "steps_completed": completed_fields,
                "total_steps": len(required_fields),
                "completion_status": "complete" if completion_percentage == 100 else "incomplete"
            },
            "timestamps": {
                "submitted_at": kyc.submitted_at.isoformat() if kyc.submitted_at else None,
                "verified_at": kyc.verified_at.isoformat() if kyc.verified_at else None,
                "last_updated": datetime.utcnow().isoformat()
            },
        "kyc_data": {
            "id": kyc.id,
            "user_id": kyc.user_id,
            
            # Personal Information
            "full_name": kyc.full_name,
            "date_of_birth": kyc.date_of_birth,
            "gender": kyc.gender,
            
            # Contact Information
            "email": kyc.email,
            "phone": kyc.phone,
            "address": kyc.address,
            "city": kyc.city,
            "state": kyc.state,
            "pin_code": kyc.pin_code,
            
            # Business Information
            "business_name": kyc.business_name,
            "business_type": kyc.business_type,
            "business_address": kyc.business_address,
            "company_pan_number": kyc.company_pan_number,
            
            # Bank Details
            "bank_name": kyc.bank_name,
            "account_number": kyc.account_number,
            "ifsc_code": kyc.ifsc_code,
            "account_holder_name": kyc.account_holder_name,
            "branch_name": kyc.branch_name,
            
            # Document Information
            "pan_card_no": kyc.pan_card_no,
            "aadhar_card_no": kyc.aadhar_card_no,
            
            # Document URLs
            "profile_photo_url": kyc.profile_photo_url,
            "aadhar_card_url": kyc.aadhar_card_url,
            "pan_card_url": kyc.pan_card_url,
            "company_pan_card_url": kyc.company_pan_card_url,
            "signature_url": kyc.signature_url,
            "business_license_url": kyc.business_license_url,
            "gst_certificate_url": kyc.gst_certificate_url,
            
            # Status and Timestamps
            "status": kyc.status,
            "submitted_at": kyc.submitted_at,
            "verified_at": kyc.verified_at,
            "rejection_reason": kyc.rejection_reason
        }
    }
    
    except SQLAlchemyError as db_error:
        logger.error(f"Database error while checking KYC status for user {current_user.id}: {db_error}")
        raise KYCErrorResponse.database_error(
            "status check",
            "Failed to retrieve KYC status from database"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error while checking KYC status for user {current_user.id}: {e}\n{traceback.format_exc()}")
        raise KYCErrorResponse.create_error_response(
            error_code="STATUS_CHECK_ERROR",
            message="Failed to check KYC status",
            details="An unexpected error occurred. Please try again or contact support",
            status_code=500
        )

@router.post("/resubmit")
async def resubmit_kyc_form(
    # Only required fields that exist in database
    aadhar_number: str = Form(..., description="Aadhar card number (required)"),
    pan_number: str = Form(..., description="PAN card number (required)"),
    
    # Optional fields (frontend sends these but we don't store them in current DB schema)
    full_name: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    pin_code: Optional[str] = Form(None),
    business_name: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    business_address: Optional[str] = Form(None),
    company_pan_number: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None),
    account_number: Optional[str] = Form(None),
    ifsc_code: Optional[str] = Form(None),
    account_holder_name: Optional[str] = Form(None),
    branch_name: Optional[str] = Form(None),
    
    # Document Files (optional)
    aadhar_card: Optional[UploadFile] = File(None),
    pan_card: Optional[UploadFile] = File(None),
    company_pan_card: Optional[UploadFile] = File(None),
    photo: Optional[UploadFile] = File(None),
    signature: Optional[UploadFile] = File(None),
    business_license: Optional[UploadFile] = File(None),
    gst_certificate: Optional[UploadFile] = File(None),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resubmit KYC form (same functionality as submit-form).
    """
    # Just call the same logic as submit-form
    return await submit_kyc_form(
        aadhar_number=aadhar_number,
        pan_number=pan_number,
        full_name=full_name,
        date_of_birth=date_of_birth,
        gender=gender,
        email=email,
        phone=phone,
        address=address,
        city=city,
        state=state,
        pin_code=pin_code,
        business_name=business_name,
        business_type=business_type,
        business_address=business_address,
        company_pan_number=company_pan_number,
        bank_name=bank_name,
        account_number=account_number,
        ifsc_code=ifsc_code,
        account_holder_name=account_holder_name,
        branch_name=branch_name,
        aadhar_card=aadhar_card,
        pan_card=pan_card,
        company_pan_card=company_pan_card,
        photo=photo,
        signature=signature,
        business_license=business_license,
        gst_certificate=gst_certificate,
        db=db,
        current_user=current_user
    )

@router.get("/list/pending")
async def list_pending_kyc(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all pending KYC requests. Only accessible by superadmin.
    """
    logger.info(f"Pending KYC list request by user {current_user.id}")
    
    try:
        # Check authorization
        allowed_roles = ["superadmin", "super_admin"]
        if current_user.role.name not in allowed_roles:
            logger.warning(f"Unauthorized pending KYC list attempt by user {current_user.id} with role {current_user.role.name}")
            return KYCErrorResponse.forbidden_error(
                message="Access to pending KYC list requires superadmin privileges",
                details={
                    "required_roles": allowed_roles,
                    "current_role": current_user.role.name,
                    "action": "contact_administrator_for_access"
                }
            )

        pending_kyc = db.query(KYCDocument).filter(
            KYCDocument.status == KYCStatus.PENDING
        ).all()
        
        logger.info(f"Retrieved {len(pending_kyc)} pending KYC documents")
        return {
            "data": pending_kyc,
            "count": len(pending_kyc),
            "status": "success",
            "message": f"Found {len(pending_kyc)} pending KYC requests"
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving pending KYC list: {str(e)}")
        return KYCErrorResponse.database_error(
            message="Failed to retrieve pending KYC requests",
            details={
                "error": "database_query_failed",
                "action": "try_again_or_contact_administrator"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving pending KYC list: {str(e)}")
        return KYCErrorResponse.database_error(
            message="An unexpected error occurred while retrieving pending KYC requests",
            details={
                "error": "unexpected_retrieval_error",
                "action": "contact_administrator"
            }
        )

@router.get("/list/all")
async def list_all_kyc(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all KYC requests regardless of status. Accessible by admin roles.
    """
    logger.info(f"All KYC list request by user {current_user.id}")
    
    try:
        # Re-enable authentication with proper error handling
        allowed_roles = ["superadmin", "super_admin", "admin", "whitelabel"]
        if current_user.role.name not in allowed_roles:
            logger.warning(f"Unauthorized KYC list attempt by user {current_user.id} with role {current_user.role.name}")
            return KYCErrorResponse.forbidden_error(
                message="Access to KYC list requires administrative privileges",
                details={
                    "required_roles": allowed_roles,
                    "current_role": current_user.role.name,
                    "action": "contact_administrator_for_access"
                }
            )

        all_kyc = db.query(KYCDocument).join(User).order_by(KYCDocument.submitted_at.desc()).all()
        
        # Return with user information
        kyc_list = []
        for kyc in all_kyc:
            kyc_data = {
                "id": kyc.id,
                "user_id": kyc.user_id,
                "user": {
                    "id": kyc.user.id,
                    "email": kyc.user.email,
                    "full_name": kyc.user.full_name,
                    "phone": kyc.user.phone,
                    "user_code": kyc.user.user_code
                },
                
                # Personal Information
                "full_name": kyc.full_name,
                "date_of_birth": kyc.date_of_birth,
                "gender": kyc.gender,
                
                # Contact Information
                "email": kyc.email,
                "phone": kyc.phone,
                "address": kyc.address,
                "city": kyc.city,
                "state": kyc.state,
                "pin_code": kyc.pin_code,
                
                # Business Information
                "business_name": kyc.business_name,
                "business_type": kyc.business_type,
                "business_address": kyc.business_address,
                "company_pan_number": kyc.company_pan_number,
                
                # Bank Details
                "bank_name": kyc.bank_name,
                "account_number": kyc.account_number,
                "ifsc_code": kyc.ifsc_code,
                "account_holder_name": kyc.account_holder_name,
                "branch_name": kyc.branch_name,
                
                # Document Information
                "pan_card_no": kyc.pan_card_no,
                "aadhar_card_no": kyc.aadhar_card_no,
                
                # Document URLs
                "profile_photo_url": kyc.profile_photo_url,
                "aadhar_card_url": kyc.aadhar_card_url,
                "pan_card_url": kyc.pan_card_url,
                "company_pan_card_url": kyc.company_pan_card_url,
                "signature_url": kyc.signature_url,
                "business_license_url": kyc.business_license_url,
                "gst_certificate_url": kyc.gst_certificate_url,
                
                # Status and Timestamps
                "status": kyc.status,
                "submitted_at": kyc.submitted_at,
                "verified_at": kyc.verified_at,
                "rejection_reason": kyc.rejection_reason
            }
            kyc_list.append(kyc_data)
    
        logger.info(f"Retrieved {len(kyc_list)} KYC documents")
        return {
            "data": kyc_list, 
            "total": len(kyc_list),
            "status": "success",
            "message": f"Found {len(kyc_list)} KYC requests"
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving all KYC list: {str(e)}")
        return KYCErrorResponse.database_error(
            message="Failed to retrieve KYC requests",
            details={
                "error": "database_query_failed",
                "action": "try_again_or_contact_administrator"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving all KYC list: {str(e)}")
        return KYCErrorResponse.database_error(
            message="An unexpected error occurred while retrieving KYC requests",
            details={
                "error": "unexpected_retrieval_error",
                "action": "contact_administrator"
            }
        )

@router.post("/{user_code}/verify", response_model=KYCResponse)
async def verify_kyc(
    user_code: str,
    verification: KYCVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify a KYC request - approve, reject, or hold.
    Actions: accept, reject, hold
    """
    logger.info(f"KYC verification request by user {current_user.id} for user_code {user_code}")
    
    try:
        # Check authorization
        allowed_roles = ["superadmin", "super_admin", "admin", "whitelabel"]
        if current_user.role.name not in allowed_roles:
            logger.warning(f"Unauthorized KYC verification attempt by user {current_user.id} with role {current_user.role.name}")
            return KYCErrorResponse.forbidden_error(
                message="KYC verification requires administrative privileges",
                details={
                    "required_roles": allowed_roles,
                    "current_role": current_user.role.name,
                    "action": "contact_administrator_for_access"
                }
            )

        # Validate user_code parameter
        if not user_code or user_code.strip() == "":
            return KYCErrorResponse.validation_error(
                message="User code is required in URL path",
                details={
                    "missing_parameter": "user_code",
                    "action": "provide_valid_user_code_in_url"
                }
            )

        # Validate verification action
        valid_actions = ["accept", "reject", "hold"]
        if verification.action not in valid_actions:
            return KYCErrorResponse.validation_error(
                message="Invalid verification action",
                details={
                    "provided_action": verification.action,
                    "valid_actions": valid_actions,
                    "action": "use_valid_verification_action"
                }
            )

        # Validate rejection reason for reject action
        if verification.action == "reject" and not verification.rejection_reason:
            return KYCErrorResponse.validation_error(
                message="Rejection reason is required when rejecting KYC",
                details={
                    "missing_field": "rejection_reason",
                    "action": "provide_rejection_reason"
                }
            )

        # First get the user, then get their KYC
        user = db.query(User).filter(User.user_code == user_code).first()
        if not user:
            logger.warning(f"User not found with user_code: {user_code}")
            return KYCErrorResponse.not_found_error(
                message="User not found with provided user code",
                details={
                    "user_code": user_code,
                    "action": "verify_user_code_exists"
                }
            )
        
        kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user.id).first()
        if not kyc:
            logger.warning(f"KYC document not found for user {user.id} (user_code: {user_code})")
            return KYCErrorResponse.not_found_error(
                message="KYC document not found for specified user",
                details={
                    "user_code": user_code,
                    "user_id": user.id,
                    "action": "ensure_user_has_submitted_kyc"
                }
            )

        # Check if KYC is in a verifiable state
        if kyc.status in [KYCStatus.CONFIRMED, KYCStatus.REJECTED] and verification.action != "hold":
            return KYCErrorResponse.business_rule_error(
                message=f"KYC already processed with status: {kyc.status}",
                details={
                    "current_status": kyc.status,
                    "requested_action": verification.action,
                    "action": "kyc_already_processed_cannot_change_unless_hold"
                }
            )

        action_status = {
            "accept": KYCStatus.CONFIRMED,  # Database has CONFIRMED, not APPROVED
            "reject": KYCStatus.REJECTED,
            "hold": KYCStatus.HOLD
        }

        previous_status = kyc.status
        kyc.status = action_status[verification.action]
        
        if verification.action == "accept":
            kyc.verified_at = datetime.utcnow()
            kyc.rejection_reason = None
            logger.info(f"KYC approved for user {user.id} (user_code: {user_code})")
        elif verification.action == "reject":
            kyc.rejection_reason = verification.rejection_reason or "No reason provided"
            kyc.verified_at = None  # Clear verification timestamp on rejection
            logger.info(f"KYC rejected for user {user.id} (user_code: {user_code}): {kyc.rejection_reason}")
        elif verification.action == "hold":
            logger.info(f"KYC put on hold for user {user.id} (user_code: {user_code})")
        
        # Save changes to database
        db.commit()
        db.refresh(kyc)
        logger.info(f"KYC status updated from {previous_status} to {kyc.status} for user {user.id}")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during KYC verification: {str(e)}")
        return KYCErrorResponse.database_error(
            message="Failed to update KYC verification status",
            details={
                "error": "database_transaction_failed",
                "user_code": user_code,
                "action": "try_again_or_contact_administrator"
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during KYC verification: {str(e)}")
        return KYCErrorResponse.database_error(
            message="An unexpected error occurred during KYC verification",
            details={
                "error": "unexpected_verification_error",
                "user_code": user_code,
                "action": "contact_administrator"
            }
        )

    # Construct proper response
    return {
        "id": kyc.id,
        "user_code": user.user_code,
        "shop_name": kyc.business_name or "",  # Map business_name to shop_name
        "business_type": kyc.business_type or "",
        "business_category": "General",  # Default value since this field doesn't exist in our model
        "gst_no": kyc.gst_certificate_url,  # Best we can do - map to GST certificate URL
        "pan_card_no": kyc.pan_card_no or "",
        "company_pan_no": kyc.company_pan_number,  # Map company_pan_number to company_pan_no
        "aadhar_card_no": kyc.aadhar_card_no or "",
        "business_registration_no": "",  # Field doesn't exist in our model
        "trade_license_no": "",  # Field doesn't exist in our model
        "profile_photo_url": kyc.profile_photo_url or "",
        "address_proof_type": "Aadhar",  # Default since we don't have this field
        "address_proof_url": kyc.aadhar_card_url,  # Map aadhar_card_url
        "company_pan_url": kyc.company_pan_card_url,  # Map company_pan_card_url
        "status": kyc.status,
        "submitted_at": kyc.submitted_at,
        "verified_at": kyc.verified_at,
        "rejection_reason": kyc.rejection_reason
    }

@router.get("/details")
async def get_current_user_kyc_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get KYC details for the current authenticated user.
    """
    logger.info(f"KYC details request by user {current_user.id}")
    
    try:
        # Validate user authentication
        if not current_user or not current_user.id:
            return KYCErrorResponse.unauthorized_error(
                message="User authentication required",
                details={
                    "action": "login_required_to_access_kyc_details"
                }
            )

        kyc = db.query(KYCDocument).filter(
            KYCDocument.user_id == current_user.id
        ).first()

        if not kyc:
            logger.info(f"No KYC document found for user {current_user.id}")
            return KYCErrorResponse.not_found_error(
                message="No KYC document found for your account",
                details={
                    "user_id": current_user.id,
                    "action": "submit_kyc_documents_first"
                }
            )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving KYC details for user {current_user.id}: {str(e)}")
        return KYCErrorResponse.database_error(
            message="Failed to retrieve KYC details",
            details={
                "error": "database_query_failed",
                "action": "try_again_or_contact_support"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving KYC details for user {current_user.id}: {str(e)}")
        return KYCErrorResponse.database_error(
            message="An unexpected error occurred while retrieving KYC details",
            details={
                "error": "unexpected_retrieval_error",
                "action": "contact_support"
            }
        )

    return {
        "id": kyc.id,
        "user_id": kyc.user_id,
        
        # Personal Information
        "full_name": kyc.full_name,
        "date_of_birth": kyc.date_of_birth,
        "gender": kyc.gender,
        
        # Contact Information
        "email": kyc.email,
        "phone": kyc.phone,
        "address": kyc.address,
        "city": kyc.city,
        "state": kyc.state,
        "pin_code": kyc.pin_code,
        
        # Business Information
        "business_name": kyc.business_name,
        "business_type": kyc.business_type,
        "business_address": kyc.business_address,
        "company_pan_number": kyc.company_pan_number,
        
        # Bank Details
        "bank_name": kyc.bank_name,
        "account_number": kyc.account_number,
        "ifsc_code": kyc.ifsc_code,
        "account_holder_name": kyc.account_holder_name,
        "branch_name": kyc.branch_name,
        
        # Document Information
        "pan_card_no": kyc.pan_card_no,
        "aadhar_card_no": kyc.aadhar_card_no,
        
        # Document URLs
        "profile_photo_url": kyc.profile_photo_url,
        "aadhar_card_url": kyc.aadhar_card_url,
        "pan_card_url": kyc.pan_card_url,
        "company_pan_card_url": kyc.company_pan_card_url,
        "signature_url": kyc.signature_url,
        "business_license_url": kyc.business_license_url,
        "gst_certificate_url": kyc.gst_certificate_url,
        
        # Status and Timestamps
        "status": kyc.status,
        "submitted_at": kyc.submitted_at,
        "verified_at": kyc.verified_at,
        "rejection_reason": kyc.rejection_reason
    }

@router.get("/{user_id}")
async def get_kyc_details_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get KYC details for a specific user. Accessible by superadmin or the user themselves.
    """
    logger.info(f"KYC details by user ID request by user {current_user.id} for user {user_id}")
    
    try:
        # Validate user_id parameter
        if not user_id or user_id <= 0:
            return KYCErrorResponse.validation_error(
                message="Invalid user ID provided",
                details={
                    "provided_user_id": user_id,
                    "action": "provide_valid_positive_user_id"
                }
            )

        # Check authorization
        if current_user.role.name != "superadmin" and current_user.id != user_id:
            logger.warning(f"Unauthorized KYC details access attempt by user {current_user.id} for user {user_id}")
            return KYCErrorResponse.forbidden_error(
                message="Not authorized to view this user's KYC details",
                details={
                    "requested_user_id": user_id,
                    "your_user_id": current_user.id,
                    "your_role": current_user.role.name,
                    "action": "can_only_view_own_kyc_or_need_superadmin_role"
                }
            )

        # Verify target user exists
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            return KYCErrorResponse.not_found_error(
                message="User not found",
                details={
                    "user_id": user_id,
                    "action": "verify_user_id_exists"
                }
            )

        kyc = db.query(KYCDocument).filter(
            KYCDocument.user_id == user_id
        ).first()

        if not kyc:
            logger.info(f"No KYC document found for user {user_id}")
            return KYCErrorResponse.not_found_error(
                message="No KYC document found for this user",
                details={
                    "user_id": user_id,
                    "action": "user_has_not_submitted_kyc_documents"
                }
            )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving KYC details for user {user_id}: {str(e)}")
        return KYCErrorResponse.database_error(
            message="Failed to retrieve KYC details",
            details={
                "error": "database_query_failed",
                "user_id": user_id,
                "action": "try_again_or_contact_administrator"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving KYC details for user {user_id}: {str(e)}")
        return KYCErrorResponse.database_error(
            message="An unexpected error occurred while retrieving KYC details",
            details={
                "error": "unexpected_retrieval_error",
                "user_id": user_id,
                "action": "contact_administrator"
            }
        )

    return {
        "id": kyc.id,
        "user_id": kyc.user_id,
        "pan_card_no": kyc.pan_card_no,
        "aadhar_card_no": kyc.aadhar_card_no,
        "profile_photo_url": kyc.profile_photo_url,
        "status": kyc.status,
        "submitted_at": kyc.submitted_at,
        "verified_at": kyc.verified_at,
        "rejection_reason": kyc.rejection_reason
    }