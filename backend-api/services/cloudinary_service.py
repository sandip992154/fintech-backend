"""
Cloudinary service — canonical module for all Cloudinary operations.

Configuration is read from environment variables:
    CLOUDINARY_CLOUD_NAME
    CLOUDINARY_API_KEY
    CLOUDINARY_API_SECRET

The KYC router uses services/utils/document_handler.py which configures
Cloudinary from the same env vars and provides the upload/delete helpers.
This module exposes a convenience class for any other service that needs
direct Cloudinary access (e.g. profile pictures, company logos).
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException

# Configure once at import time
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


class CloudinaryService:
    """Direct Cloudinary upload/delete helpers used outside the KYC router."""

    @staticmethod
    async def upload_profile_photo(file: UploadFile, user_id: int) -> str:
        """Upload a profile photo and return the Cloudinary secure_url."""
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 5 MB")

        try:
            result = cloudinary.uploader.upload(
                content,
                folder="profile_photos",
                public_id=f"user_{user_id}_profile",
                transformation=[
                    {"width": 300, "height": 300, "crop": "fill", "gravity": "face"},
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"},
                ],
                overwrite=True,
                invalidate=True,
            )
            return result["secure_url"]
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")

    @staticmethod
    async def upload_document(
        file: UploadFile, user_id: int, document_type: str
    ) -> str:
        """Upload a document (image or PDF) and return the Cloudinary secure_url."""
        allowed = ["image/", "application/pdf"]
        if not file.content_type or not any(
            file.content_type.startswith(t) for t in allowed
        ):
            raise HTTPException(
                status_code=400, detail="File must be an image or PDF"
            )

        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, detail="File size must be less than 10 MB"
            )

        try:
            result = cloudinary.uploader.upload(
                content,
                folder=f"documents/{document_type}",
                public_id=f"user_{user_id}_{document_type}",
                resource_type="auto",
                overwrite=True,
                invalidate=True,
            )
            return result["secure_url"]
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"Document upload failed: {exc}"
            )

    @staticmethod
    def delete_file(public_id: str) -> bool:
        """Destroy a Cloudinary asset by public_id. Returns True on success."""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception as exc:
            print(f"Error deleting Cloudinary asset '{public_id}': {exc}")
            return False
