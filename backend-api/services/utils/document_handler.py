import os
import shutil
from fastapi import UploadFile, HTTPException
from typing import List
import uuid
from datetime import datetime
from PIL import Image
import filetype
import aiofiles

UPLOAD_DIR = "static/uploads"
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"]
ALLOWED_DOC_TYPES = ["application/pdf"]
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_DOC_SIZE = 5 * 1024 * 1024    # 5MB

# Create directories if they don't exist
os.makedirs(f"{UPLOAD_DIR}/profile_photos", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/pan_cards", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/company_pan", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/aadhar_cards", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/address_proofs", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/signatures", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/business_licenses", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/gst_certificates", exist_ok=True)

async def validate_file(file: UploadFile, doc_type: str):
    """Validate file type and size"""
    # Read file content
    content = await file.read()
    await file.seek(0)  # Reset file pointer
    
    # Check file size
    size_limit = MAX_IMAGE_SIZE if doc_type == "profile_photo" else MAX_DOC_SIZE
    if len(content) > size_limit:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {size_limit/1024/1024}MB limit"
        )
    
    # Check file type
    kind = filetype.guess(content)
    if kind is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot determine file type or file type not supported"
        )
    
    file_type = kind.mime
    if doc_type == "profile_photo" and file_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    elif doc_type != "profile_photo" and file_type not in ALLOWED_IMAGE_TYPES + ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES + ALLOWED_DOC_TYPES)}"
        )

async def process_profile_photo(file: UploadFile) -> str:
    """Process and save profile photo"""
    # Validate file
    await validate_file(file, "profile_photo")
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = f"{UPLOAD_DIR}/profile_photos/{filename}"
    
    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Resize image to passport size (60px X 80px)
    with Image.open(filepath) as img:
        img = img.resize((60, 80))
        img.save(filepath)
    
    return f"/static/uploads/profile_photos/{filename}"

async def save_document(file: UploadFile, doc_type: str, user_id: int) -> str:
    """Save document and return URL"""
    # Validate file
    await validate_file(file, doc_type)
    
    # Map document types to directories
    type_dirs = {
        "pan_card": "pan_cards",
        "company_pan": "company_pan",
        "company_pan_card": "company_pan",
        "aadhar_card": "aadhar_cards",
        "address_proof": "address_proofs",
        "photo": "profile_photos",
        "signature": "signatures",
        "business_license": "business_licenses",
        "gst_certificate": "gst_certificates"
    }
    
    if doc_type not in type_dirs:
        raise HTTPException(status_code=400, detail=f"Invalid document type: {doc_type}. Allowed types: {', '.join(type_dirs.keys())}")
    
    # Generate unique filename with user_id
    ext = os.path.splitext(file.filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user{user_id}_{timestamp}{ext}"
    filepath = f"{UPLOAD_DIR}/{type_dirs[doc_type]}/{filename}"
    
    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return f"/static/uploads/{type_dirs[doc_type]}/{filename}"

async def delete_document(file_url: str):
    """Delete document from storage"""
    if not file_url:
        return
        
    try:
        file_path = os.path.join("static", file_url.split("/static/")[1])
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {file_url}: {str(e)}")