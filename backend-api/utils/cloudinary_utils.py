"""
Cloudinary utilities — thin wrappers that delegate to document_handler.

Import document_handler directly in new code. This module exists only for
backward compatibility with any code that imports from utils.cloudinary_utils.
"""
from services.utils.document_handler import (
    process_profile_photo,
    save_document,
    upload_image,
    delete_document,
    _extract_public_id as _extract_public_id_from_url,
    FOLDER_MAP,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_DOC_TYPES,
)
import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile


def configure_cloudinary():
    """No-op: Cloudinary is configured at import time in document_handler."""
    pass  # config already applied


def validate_file(file: UploadFile, document_type: str) -> None:
    """Synchronous pre-check on content_type (async full validation is in document_handler)."""
    from config.constants import FILE_UPLOAD_CONFIG
    if file.size and file.size > FILE_UPLOAD_CONFIG["MAX_SIZE_MB"] * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {FILE_UPLOAD_CONFIG['MAX_SIZE_MB']} MB",
        )
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    dangerous = [".exe", ".bat", ".cmd", ".scr", ".pif"]
    if any(file.filename.lower().endswith(ext) for ext in dangerous):
        raise HTTPException(status_code=400, detail="File type not allowed")


def upload_to_cloudinary(file: UploadFile, folder: str = "uploads"):
    """Synchronous upload helper (use process_profile_photo / save_document for async)."""
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type="auto",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            quality="auto:good",
            fetch_format="auto",
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File upload failed: {exc}")


def delete_from_cloudinary(public_id: str) -> bool:
    """Delete a Cloudinary asset by public_id."""
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as exc:
        print(f"Failed to delete Cloudinary asset '{public_id}': {exc}")
        return False
