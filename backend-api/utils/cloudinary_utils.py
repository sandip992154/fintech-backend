"""
Cloudinary utilities for file upload and validation
"""
import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile
import os
from typing import Dict, Any

from config.constants import FILE_UPLOAD_CONFIG

# Initialize Cloudinary (will be configured via environment variables)
def configure_cloudinary():
    """Configure Cloudinary with environment variables"""
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )

def validate_file(file: UploadFile, document_type: str) -> None:
    """Validate uploaded file"""
    # Check file size
    if file.size > FILE_UPLOAD_CONFIG["MAX_SIZE_MB"] * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File size too large. Maximum size is {FILE_UPLOAD_CONFIG['MAX_SIZE_MB']}MB"
        )
    
    # Check file type
    if file.content_type not in FILE_UPLOAD_CONFIG["ALLOWED_TYPES"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(FILE_UPLOAD_CONFIG['ALLOWED_TYPES'])}"
        )
    
    # Document-specific validation
    if document_type in ["pan_card_front", "pan_card_back", "aadhar_front", "aadhar_back", "photo", "signature"]:
        if file.content_type == "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"{document_type} must be an image file"
            )
    
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Check for potentially malicious files
    dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif']
    if any(file.filename.lower().endswith(ext) for ext in dangerous_extensions):
        raise HTTPException(status_code=400, detail="File type not allowed")

def upload_to_cloudinary(file: UploadFile, folder: str = "uploads") -> Dict[str, Any]:
    """Upload file to Cloudinary"""
    try:
        # Configure Cloudinary if not already configured
        if not cloudinary.config().cloud_name:
            configure_cloudinary()
        
        # Upload file
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type="auto",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            quality="auto:good",
            fetch_format="auto"
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )

def delete_from_cloudinary(public_id: str) -> bool:
    """Delete file from Cloudinary"""
    try:
        # Configure Cloudinary if not already configured
        if not cloudinary.config().cloud_name:
            configure_cloudinary()
        
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    
    except Exception as e:
        print(f"Failed to delete file from Cloudinary: {str(e)}")
        return False

def get_file_info(public_id: str) -> Dict[str, Any]:
    """Get file information from Cloudinary"""
    try:
        # Configure Cloudinary if not already configured
        if not cloudinary.config().cloud_name:
            configure_cloudinary()
        
        result = cloudinary.api.resource(public_id)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {str(e)}"
        )