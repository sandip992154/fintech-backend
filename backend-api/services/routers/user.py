from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.database import get_db
from services.models.models import (
    User, BankAccount, CompanyDetails, Role
)
from services.models.user_models import KYCDocument
from services.models.transaction_models import ServiceProvider
from services.schemas.schemas import *
from services.auth.auth import verify_password, get_password_hash, get_current_user
from typing import List
from utils.email_utils import send_account_email
from utils.error_handlers import APIErrorResponse, handle_database_exceptions, validate_required_fields, validate_user_permissions
from config import email_config
from fastapi import Body
from fastapi import Query
import logging

router = APIRouter(tags=["Users"])
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ================================ KYC Workflow ===================================



@router.post("/kyc/submit", response_model=KYCOut, status_code=status.HTTP_201_CREATED)
def submit_kyc(payload: KYCCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    User submits KYC form. Status is set to 'pending'.
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not hasattr(user, 'hashed_pin') or not user.hashed_pin:
        raise HTTPException(status_code=400, detail="User has no PIN set")
    if not verify_password(payload.pin, user.hashed_pin or ""):
        raise HTTPException(status_code=403, detail="Invalid security PIN")
    # Check for duplicate GST or Aadhaar for other users
    if payload.gst_no:
        gst_exists = db.query(KYCDocument).filter(KYCDocument.gst_no == payload.gst_no, KYCDocument.user_id != user.id).first()
        if gst_exists:
            raise HTTPException(status_code=400, detail="GST number already used by another user")
    if payload.aadhar_card_no:
        aadhar_exists = db.query(KYCDocument).filter(KYCDocument.aadhar_card_no == payload.aadhar_card_no, KYCDocument.user_id != user.id).first()
        if aadhar_exists:
            raise HTTPException(status_code=400, detail="Aadhaar number already used by another user")
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user.id).first()
    if kyc:
        kyc.shop_name = payload.shop_name
        kyc.gst_no = payload.gst_no
        kyc.aadhar_card_no = payload.aadhar_card_no
        kyc.status = "pending"
        kyc.rejection_reason = None
    else:
        kyc = KYCDocument(
            user_id=user.id,
            shop_name=payload.shop_name,
            gst_no=payload.gst_no,
            aadhar_card_no=payload.aadhar_card_no,
            status="pending"
        )
        db.add(kyc)
    db.commit()
    db.refresh(kyc)

    # Notify all superadmins by email
    superadmins = db.query(User).join(Role).filter(Role.name == "superadmin").all()
    for admin in superadmins:
        try:
            send_account_email(
                admin,
                None,
                "kyc_new_request",
                extra_message=f"A new KYC request has been submitted by user {user.full_name} (ID: {user.id}, Email: {user.email})."
            )
        except Exception:
            pass

    return kyc

@router.get("/kyc/list", response_model=List[KYCOut])
def list_pending_kyc(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Super admin lists all pending KYC requests.
    """
    if getattr(current_user.role, 'name', None) != "superadmin":
        raise HTTPException(status_code=403, detail="Not authorized")
    pending_kyc = db.query(KYCDocument).filter(KYCDocument.status == "pending").all()
    return pending_kyc

@router.post("/kyc/{kyc_id}/verify")
def verify_kyc(
    kyc_id: int,
    action: str = Body(..., embed=True, description="Action: accept/reject/hold"),
    rejection_reason: str = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Super admin verifies (accept/reject/hold) a KYC request.
    """
    if getattr(current_user.role, 'name', None) != "superadmin":
        raise HTTPException(status_code=403, detail="Not authorized")
    kyc = db.query(KYCDocument).filter(KYCDocument.id == kyc_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC not found")
    user = db.query(User).filter(User.id == kyc.user_id).first()
    if action == "accept":
        kyc.status = "confirmed"
        kyc.verified_at = func.now()
        kyc.rejection_reason = None
    elif action == "reject":
        kyc.status = "rejected"
        kyc.rejection_reason = rejection_reason or "No reason provided"
        # Send rejection email
        if user:
            from utils.email_utils import send_account_email
            send_account_email(user, None, "kyc_rejected", extra_message=f"Your KYC is rejected. Reason: {kyc.rejection_reason}")
    elif action == "hold":
        kyc.status = "hold"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    db.commit()
    db.refresh(kyc)
    return {"id": kyc.id, "status": kyc.status, "rejection_reason": kyc.rejection_reason}

@router.get("/kyc/status")
def kyc_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    User checks their KYC status with detailed information.
    """
    logger.info(f"KYC status check by user {current_user.id}")
    
    try:
        # Validate user authentication
        if not current_user or not current_user.id:
            raise APIErrorResponse.unauthorized_error(
                message="User authentication required to check KYC status",
                details={
                    "action": "login_required"
                }
            )

        kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
        
        if not kyc:
            logger.info(f"No KYC found for user {current_user.id}")
            return {
                "status": "not_submitted",
                "message": "You have not submitted KYC documents yet",
                "action": "submit_kyc_documents_to_continue",
                "details": {
                    "user_id": current_user.id,
                    "next_step": "complete_kyc_submission"
                }
            }

        # Build detailed status response
        status_responses = {
            "pending": {
                "status": "pending",
                "message": "Your KYC documents are under review",
                "action": "wait_for_admin_verification",
                "details": {
                    "submitted_at": kyc.submitted_at,
                    "estimated_review_time": "1-3 business days"
                }
            },
            "confirmed": {
                "status": "confirmed",
                "message": "KYC approved successfully. Full dashboard access granted",
                "action": "access_all_features_now_available",
                "details": {
                    "approved_at": kyc.verified_at,
                    "submitted_at": kyc.submitted_at,
                    "verification_complete": True
                }
            },
            "rejected": {
                "status": "rejected",
                "message": f"Your KYC has been rejected",
                "action": "review_rejection_reason_and_resubmit",
                "details": {
                    "rejection_reason": kyc.rejection_reason or "No specific reason provided",
                    "submitted_at": kyc.submitted_at,
                    "can_resubmit": True
                }
            },
            "hold": {
                "status": "hold",
                "message": "Your KYC is temporarily on hold",
                "action": "contact_support_for_assistance",
                "details": {
                    "submitted_at": kyc.submitted_at,
                    "support_contact": "support@bandarupay.com"
                }
            }
        }

        response = status_responses.get(kyc.status, {
            "status": kyc.status,
            "message": f"KYC status: {kyc.status}",
            "action": "contact_support_for_status_clarification",
            "details": {
                "submitted_at": kyc.submitted_at,
                "unknown_status": True
            }
        })

        logger.info(f"KYC status '{kyc.status}' returned for user {current_user.id}")
        return response

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving KYC status for user {current_user.id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="Failed to retrieve KYC status",
            details={
                "error": "database_query_failed",
                "user_id": current_user.id,
                "action": "try_again_or_contact_support"
            }
        )
    except HTTPException:
        # Re-raise APIErrorResponse exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving KYC status for user {current_user.id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="An unexpected error occurred while checking KYC status",
            details={
                "error": "unexpected_kyc_status_error",
                "user_id": current_user.id,
                "action": "contact_support"
            }
        )

@router.put("update_user/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        # Verify PIN
        if not user.hashed_pin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no PIN set")
        if not pwd_context.verify(user_in.pin, user.hashed_pin):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")
        update_data = user_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error updating user: {str(e)}")

@router.post("/users/{user_id}/bank-account")
def add_or_update_bank_account(user_id: int, account_data: BankAccountCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # Verify PIN
        if not user.hashed_pin or not verify_password(account_data.pin, user.hashed_pin):
            raise HTTPException(status_code=403, detail="Invalid PIN")
        encrypted_account_number = get_password_hash(account_data.account_number)
        existing_account = db.query(BankAccount).filter(BankAccount.user_id == user.id).first()
        if existing_account:
            existing_account.bank_name = account_data.bank_name
            existing_account.ifsc = account_data.ifsc
            existing_account.account_holder = account_data.account_holder
            existing_account.account_number_encrypted = encrypted_account_number
        else:
            new_account = BankAccount(
                user_id=user.id,
                bank_name=account_data.bank_name,
                ifsc=account_data.ifsc,
                account_holder=account_data.account_holder,
                account_number_encrypted=encrypted_account_number,
            )
            db.add(new_account)
        db.commit()
        return {"message": "Bank account saved successfully"}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error saving bank account: {str(e)}")

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, user_id: int, db: Session = Depends(get_db)):
    """
    Change user password with security PIN verification.
    """
    logger.info(f"Password change request for user ID: {user_id}")
    
    try:
        # Validate input data
        if not req.old_password or not req.new_password or not req.security_pin:
            raise APIErrorResponse.validation_error(
                message="All fields are required for password change",
                details={
                    "required_fields": ["old_password", "new_password", "security_pin"],
                    "action": "provide_all_required_fields"
                }
            )

        # Validate user ID
        if not user_id or user_id <= 0:
            raise APIErrorResponse.validation_error(
                message="Invalid user ID provided",
                details={
                    "provided_user_id": user_id,
                    "action": "provide_valid_user_id"
                }
            )

        # Validate password strength
        if len(req.new_password) < 8:
            raise APIErrorResponse.validation_error(
                message="New password must be at least 8 characters long",
                details={
                    "password_length": len(req.new_password),
                    "minimum_length": 8,
                    "action": "use_stronger_password"
                }
            )

        # Check if new password is different from old password
        if req.old_password == req.new_password:
            raise APIErrorResponse.business_rule_error(
                message="New password must be different from old password",
                details={
                    "action": "choose_different_password"
                }
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found with ID: {user_id}")
            raise APIErrorResponse.not_found_error(
                message="User not found",
                details={
                    "user_id": user_id,
                    "action": "verify_user_id_exists"
                },
                resource_type="user"
            )

        # Verify security PIN
        if not user.hashed_pin:
            raise APIErrorResponse.business_rule_error(
                message="Security PIN is not set for this user",
                details={
                    "action": "setup_security_pin_first"
                }
            )

        if not verify_password(req.security_pin, user.hashed_pin):
            logger.warning(f"Invalid security PIN attempt for user ID: {user_id}")
            raise APIErrorResponse.forbidden_error(
                message="Invalid security PIN",
                details={
                    "action": "provide_correct_security_pin"
                }
            )

        # Verify old password
        if not verify_password(req.old_password, user.hashed_password):
            logger.warning(f"Invalid old password attempt for user ID: {user_id}")
            raise APIErrorResponse.forbidden_error(
                message="Current password is incorrect",
                details={
                    "action": "provide_correct_current_password"
                }
            )

        # Update password
        user.hashed_password = get_password_hash(req.new_password)
        db.commit()
        
        logger.info(f"Password successfully changed for user ID: {user_id}")
        return {
            "message": "Password changed successfully",
            "status": "success",
            "user_id": user_id
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during password change for user {user_id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="Failed to update password",
            details={
                "error": "database_transaction_failed",
                "user_id": user_id,
                "action": "try_again_or_contact_support"
            }
        )
    except HTTPException:
        # Re-raise APIErrorResponse exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password change for user {user_id}: {str(e)}")
        raise APIErrorResponse.database_error(
            message="An unexpected error occurred during password change",
            details={
                "error": "unexpected_password_change_error",
                "user_id": user_id,
                "action": "contact_support"
            }
        )

# ================================ kyc details ===================================

@router.post("/users/add_or_update_kyc/{user_id}/", response_model=KYCOut, status_code=status.HTTP_201_CREATED)
def create_or_replace_kyc(user_id: int, payload: KYCCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not verify_password(payload.pin, user.hashed_pin or ""):
            raise HTTPException(status_code=403, detail="Invalid security PIN")
        new_kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user.id).first()
        if new_kyc:
            new_kyc.shop_name = payload.shop_name
            new_kyc.gst_no = payload.gst_no
            new_kyc.aadhar_card_no = payload.aadhar_card_no
            new_kyc.status = "pending"  # Always set to pending on user update
            new_kyc.rejection_reason = None
        else:
            new_kyc = KYCDocument(
                user_id = user.id,
                shop_name = payload.shop_name,
                gst_no = payload.gst_no,
                aadhar_card_no = payload.aadhar_card_no,
                status = "pending"  # Always set to pending on user create
            )
            db.add(new_kyc)
        db.commit()
        db.refresh(new_kyc)
        return new_kyc
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error saving KYC: {str(e)}")

@router.post("/users/get_kyc/{user_id}/", response_model=KYCOut, status_code=status.HTTP_201_CREATED)
def get_kyc(user_id: int, db: Session = Depends(get_db)):
    try:
        existing = db.query(KYCDocument).filter(KYCDocument.user_id == user_id).first()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC not found")
        return existing
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching KYC: {str(e)}")

# User checks their own KYC status and gets dashboard access only if confirmed.
@router.get("/kyc/my-status", response_model=KYCOut)
def get_my_kyc_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    User checks their own KYC status and gets dashboard access only if confirmed.
    """
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="You have not submitted KYC.")
    if kyc.status == "confirmed":
        return kyc  # User can access dashboard (frontend should check status==confirmed)
    elif kyc.status == "pending":
        raise HTTPException(status_code=403, detail="Your KYC is under review. Dashboard access denied.")
    elif kyc.status == "rejected":
        raise HTTPException(status_code=403, detail=f"Your KYC is rejected. Reason: {kyc.rejection_reason}")
    elif kyc.status == "hold":
        raise HTTPException(status_code=403, detail="Your KYC is on hold. Please contact support.")
    else:
        raise HTTPException(status_code=403, detail="Unknown KYC status. Dashboard access denied.")


# Update KYC
@router.put("/users/update_kyc/{user_id}/", response_model=KYCOut)
def update_kyc(user_id: int, payload: KYCUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only allow self or admin
    if current_user.id != user_id and getattr(current_user.role, 'name', None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this KYC")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(payload.pin, user.hashed_pin or ""):
        raise HTTPException(status_code=403, detail="Invalid security PIN")
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC not found")
    for key, value in payload.dict(exclude_unset=True).items():
        if key != "pin" and key != "status":  # Prevent user from updating status
            setattr(kyc, key, value)
    kyc.status = "pending"  # Always set to pending on user update
    kyc.rejection_reason = None
    db.commit()
    db.refresh(kyc)
    return kyc

@router.delete("/users/delete_kyc/{user_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_kyc(user_id: int, pin: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only allow self or admin
    if current_user.id != user_id and getattr(current_user.role, 'name', None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this KYC")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(pin, user.hashed_pin or ""):
        raise HTTPException(status_code=403, detail="Invalid security PIN")
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC not found")
    db.delete(kyc)
    db.commit()
    return

# ---------- Company Details api ----------
# Create Company
@router.post("/companies/", response_model=CompanyOut)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    try:
        data = payload.model_dump()
        # Convert HttpUrl to str if present
        if "company_website" in data and data["company_website"] is not None:
            data["company_website"] = str(data["company_website"])
        new_company = CompanyDetails(**data)
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        return new_company
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error creating company: {str(e)}")

# Get All Companies
@router.get("/companies/", response_model=List[CompanyOut])
def get_companies(db: Session = Depends(get_db)):
    try:
        return db.query(CompanyDetails).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching companies: {str(e)}")

# Update Company
@router.put("/companies/{company_id}", response_model=CompanyOut)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    try:
        company = db.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        for key, value in payload.dict(exclude_unset=True).items():
            setattr(company, key, value)
        db.commit()
        db.refresh(company)
        return company
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error updating company: {str(e)}")

# company status update
@router.put("/companies/status/{company_id}/")
def change_company_status(company_id: int, status: CompanyStatus, db: Session = Depends(get_db)):
    try:
        company = db.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        company.status = status
        db.commit()
        db.refresh(company)
        return {"id": company.id, "name": company.company_name, "status": company.status}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error changing company status: {str(e)}")

# Update Company Details API
@router.put("/companies/update_company_details/{company_id}/", response_model=CompanyOut)
def update_company_details(company_id: int, payload: CompanyDetailsUpdate, db: Session = Depends(get_db)):
    try:
        company = db.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(company, key, value)
        db.commit()
        db.refresh(company)
        return company
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error updating company details: {str(e)}")

# Update Company News API
@router.put("/companies/update_company_news/{company_id}/", response_model=CompanyOut)
def update_company_news(company_id: int, payload: CompanyNewsUpdate, db: Session = Depends(get_db)):
    try:
        company = db.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        company.company_news = payload.company_news
        company.company_bill_notice = payload.company_bill_notice
        db.commit()
        db.refresh(company)
        return company
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error updating company news: {str(e)}")

# Update Company Support Details API
@router.put("/companies/update_company_support_details/{company_id}/", response_model=CompanySupportDetailsOut)
def update_company_support_details(company_id: int, payload: CompanySupportDetailsUpdate, db: Session = Depends(get_db)):
    try:
        company = db.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        company.company_contact_no = payload.company_contact_no
        company.company_email = payload.company_email
        db.commit()
        db.refresh(company)
        return CompanySupportDetailsOut(
            id=company.id,
            company_name=company.company_name,
            company_contact_no=company.company_contact_no,
            company_email=company.company_email
        )
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error updating company support details: {str(e)}")

# ---------- Add owner api ----------

# Add WhiteLabel API
@router.post("/whitelabel/add", response_model=WhiteLabelOut)
def add_whitelabel(payload: WhiteLabelCreate, db: Session = Depends(get_db)):
    try:
        # Check uniqueness for aadhar_card and pancard
        if db.query(User).filter(User.aadhar_card == payload.aadhar_card).first():
            raise HTTPException(status_code=400, detail="Aadhar card already exists")
        if db.query(User).filter(User.pancard == payload.pancard).first():
            raise HTTPException(status_code=400, detail="PAN card already exists")

        # Check if role exists
        role = db.query(Role).filter(Role.id == payload.role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail="Role not found")

        new_user = User(
            username=payload.mobile,  # Assuming username is mobile for whitelabel
            mobile=payload.mobile,
            email=payload.email,
            first_name=payload.name,
            state=payload.state,
            address=payload.address,
            city=payload.city,
            postal_code=payload.pincode,
            shop_name=payload.shop_name,
            pancard=payload.pancard,
            aadhar_card=payload.aadhar_card,
            company_name=payload.company_name,
            domain=payload.domain,
            role_id=payload.role_id,
            hashed_password=get_password_hash("defaultpassword"),  # Set a default password or generate one
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        # Send signup email
        send_account_email(new_user, "defaultpassword", role.name)
        return WhiteLabelOut(
            id=new_user.id,
            name=new_user.first_name,
            mobile=new_user.mobile,
            email=new_user.email,
            state=new_user.state,
            address=new_user.address,
            city=new_user.city,
            pincode=new_user.postal_code,
            shop_name=new_user.shop_name,
            pancard=new_user.pancard,
            aadhar_card=new_user.aadhar_card,
            company_name=new_user.company_name,
            domain=new_user.domain,
            role_id=new_user.role_id
        )
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error adding whitelabel: {str(e)}")

# Add Member API
@router.post("/members/add", response_model=MemberOut)
def add_member(payload: MemberCreate, db: Session = Depends(get_db)):
    try:
        # Check uniqueness for aadhar_card and pancard
        if db.query(User).filter(User.aadhar_card == payload.aadhar_card).first():
            raise HTTPException(status_code=400, detail="Aadhar card already exists")
        if db.query(User).filter(User.pancard == payload.pancard).first():
            raise HTTPException(status_code=400, detail="PAN card already exists")

        new_user = User(
            username=payload.mobile,
            mobile=payload.mobile,
            email=payload.email,
            first_name=payload.name,
            state=payload.state,
            address=payload.address,
            city=payload.city,
            postal_code=payload.pincode,
            shop_name=payload.shop_name,
            pancard=payload.pancard,
            aadhar_card=payload.aadhar_card,
            hashed_password=get_password_hash("defaultpassword"),
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        # Send signup email
        send_account_email(new_user, "defaultpassword", "member")
        return MemberOut(
            id=new_user.id,
            name=new_user.first_name,
            mobile=new_user.mobile,
            email=new_user.email,
            state=new_user.state,
            address=new_user.address,
            city=new_user.city,
            pincode=new_user.postal_code,
            shop_name=new_user.shop_name,
            pancard=new_user.pancard,
            aadhar_card=new_user.aadhar_card
        )
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error adding member: {str(e)}")

# Add Provider API
@router.post("/providers/add", response_model=ProviderOut)
def add_provider(payload: ProviderCreate, db: Session = Depends(get_db)):
    try:
        new_provider = ServiceProvider(
            provider_name=payload.provider_name,
            provider_type=payload.provider_type,
            status=payload.status,
            charge_type=payload.charge_type
        )
        db.add(new_provider)
        db.commit()
        db.refresh(new_provider)
        return ProviderOut(
            id=new_provider.id,
            provider_name=new_provider.provider_name,
            provider_type=new_provider.provider_type,
            status=new_provider.status,
            charge_type=new_provider.charge_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error adding provider: {str(e)}")

@router.put("/providers/update/{provider_id}", response_model=ProviderOut)
def update_provider(provider_id: int, payload: ProviderUpdate, db: Session = Depends(get_db)):
    try:
        provider = db.query(ServiceProvider).filter(ServiceProvider.id == provider_id).first()
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(provider, key, value)
        db.commit()
        db.refresh(provider)
        return ProviderOut(
            id=provider.id,
            provider_name=provider.provider_name,
            provider_type=provider.provider_type,
            status=provider.status,
            charge_type=provider.charge_type
        )
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error updating provider: {str(e)}")

