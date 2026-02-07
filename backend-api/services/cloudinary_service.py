"""
Cloudinary configuration and service for file uploads
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException
import os
from typing import Optional

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "your-cloud-name"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "your-api-key"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "your-api-secret"),
    secure=True
)

class CloudinaryService:
    """Service for handling Cloudinary uploads"""
    
    @staticmethod
    async def upload_profile_photo(file: UploadFile, user_id: int) -> str:
        """Upload profile photo to Cloudinary"""
        try:
            # Validate file type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            # Validate file size (5MB max)
            file_content = await file.read()
            if len(file_content) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size must be less than 5MB")
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_content,
                folder="profile_photos",
                public_id=f"user_{user_id}_profile",
                transformation=[
                    {"width": 300, "height": 300, "crop": "fill", "gravity": "face"},
                    {"quality": "auto:good"},
                    {"format": "jpg"}
                ],
                overwrite=True,
                invalidate=True
            )
            
            return result["secure_url"]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    @staticmethod
    async def upload_document(file: UploadFile, user_id: int, document_type: str) -> str:
        """Upload document to Cloudinary"""
        try:
            # Validate file type
            allowed_types = ['image/', 'application/pdf']
            if not file.content_type or not any(file.content_type.startswith(t) for t in allowed_types):
                raise HTTPException(status_code=400, detail="File must be an image or PDF")
            
            # Validate file size (10MB max for documents)
            file_content = await file.read()
            if len(file_content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size must be less than 10MB")
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_content,
                folder=f"documents/{document_type}",
                public_id=f"user_{user_id}_{document_type}",
                resource_type="auto",
                overwrite=True,
                invalidate=True
            )
            
            return result["secure_url"]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")
    
    @staticmethod
    def delete_file(public_id: str) -> bool:
        """Delete file from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False