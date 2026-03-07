"""
Document handler — all uploads go to Cloudinary.
Local filesystem is NOT used for image/document storage.

Handles ALL image and document uploads project-wide:
  - KYC documents (ID proofs, signatures, etc.)
  - Profile photos (users and superadmin)
  - Company logos and branding assets
  - Service / operator icons
  - Any other image or PDF the application needs to store
"""
import os
import re
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
import filetype

# ---------------------------------------------------------------------------
# Cloudinary configuration (reads from environment variables)
# ---------------------------------------------------------------------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]
ALLOWED_DOC_TYPES   = ["application/pdf"]
MAX_IMAGE_SIZE = 5  * 1024 * 1024   # 5 MB
MAX_DOC_SIZE   = 10 * 1024 * 1024   # 10 MB

# Cloudinary folder mapping — covers KYC documents AND all other upload categories
FOLDER_MAP = {
    # ── KYC documents ────────────────────────────────────────────────────────
    "profile_photo":    "kyc/profile_photos",
    "photo":            "kyc/profile_photos",
    "pan_card":         "kyc/pan_cards",
    "company_pan":      "kyc/company_pan",
    "company_pan_card": "kyc/company_pan",
    "aadhar_card":      "kyc/aadhar_cards",
    "address_proof":    "kyc/address_proofs",
    "signature":        "kyc/signatures",
    "business_license": "kyc/business_licenses",
    "gst_certificate":  "kyc/gst_certificates",

    # ── Branding / company assets ────────────────────────────────────────────
    "company_logo":     "company/logos",
    "company_banner":   "company/banners",
    "company_notice":   "company/notices",

    # ── Service / operator icons ─────────────────────────────────────────────
    "service_icon":     "services/icons",
    "operator_icon":    "services/operators",
    "bank_logo":        "services/banks",

    # ── Miscellaneous ────────────────────────────────────────────────────────
    "quick_link_icon":  "setup/quick_links",
    "permission_icon":  "setup/permissions",
    "general":          "uploads/general",
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _read_and_validate(file: UploadFile, doc_type: str) -> bytes:
    """Read file bytes, validate size and MIME type. Returns raw bytes."""
    content = await file.read()
    await file.seek(0)

    is_photo = doc_type in ("profile_photo", "photo")
    size_limit = MAX_IMAGE_SIZE if is_photo else MAX_DOC_SIZE
    if len(content) > size_limit:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {size_limit // (1024 * 1024)} MB limit",
        )

    kind = filetype.guess(content)
    if kind is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot determine file type. Only JPEG, PNG, and PDF are supported.",
        )

    mime = kind.mime
    allowed = ALLOWED_IMAGE_TYPES if is_photo else ALLOWED_IMAGE_TYPES + ALLOWED_DOC_TYPES
    if mime not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{mime}'. Allowed: {', '.join(allowed)}",
        )

    return content


def _extract_public_id(url: str) -> str | None:
    """Extract Cloudinary public_id (with folder, without extension) from a secure_url.

    Example URL:
        https://res.cloudinary.com/dzsuwcti4/image/upload/v1234567890/kyc/pan_cards/file.jpg
        → public_id = "kyc/pan_cards/file"
    """
    match = re.search(r"upload/(?:v\d+/)?(.+?)(?:\.[a-zA-Z0-9]+)?$", url)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Public API — used by kyc.py router
# ---------------------------------------------------------------------------

async def process_profile_photo(file: UploadFile) -> str:
    """Upload profile photo to Cloudinary with face-fill crop. Returns secure_url."""
    content = await _read_and_validate(file, "profile_photo")

    try:
        result = cloudinary.uploader.upload(
            content,
            folder=FOLDER_MAP["profile_photo"],
            resource_type="image",
            transformation=[
                {"width": 300, "height": 400, "crop": "fill", "gravity": "face"},
                {"quality": "auto:good"},
                {"fetch_format": "auto"},
            ],
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        return result["secure_url"]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Profile photo upload to Cloudinary failed: {exc}",
        )


async def save_document(file: UploadFile, doc_type: str, user_code: str) -> str:
    """Upload a KYC document to Cloudinary. Returns secure_url."""
    if doc_type not in FOLDER_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type '{doc_type}'. Allowed: {', '.join(FOLDER_MAP)}",
        )

    content = await _read_and_validate(file, doc_type)

    try:
        result = cloudinary.uploader.upload(
            content,
            folder=FOLDER_MAP[doc_type],
            resource_type="auto",          # handles both images and PDFs
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            quality="auto:good",
        )
        return result["secure_url"]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"{doc_type} upload to Cloudinary failed: {exc}",
        )


async def delete_document(file_url: str) -> None:
    """Delete a document from Cloudinary given its secure_url.

    Silently skips legacy local paths (starting with /static/) so that
    existing local-stored records don't cause errors.
    """
    if not file_url:
        return

    # Legacy local path — skip silently
    if file_url.startswith("/static/"):
        return

    public_id = _extract_public_id(file_url)
    if not public_id:
        return

    # Detect resource type: PDFs are stored as 'raw' in Cloudinary
    resource_type = "raw" if file_url.endswith(".pdf") else "image"
    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    except Exception as exc:
        # Non-fatal: log and continue
        print(f"Warning: could not delete Cloudinary asset '{public_id}': {exc}")


async def upload_image(
    file: UploadFile,
    category: str = "general",
    *,
    width: int | None = None,
    height: int | None = None,
    crop: str = "limit",
) -> str:
    """General-purpose image upload to Cloudinary.

    Use this for any image that doesn't fit the KYC document flow:
    company logos, service icons, banners, quick-link icons, etc.

    Args:
        file:     FastAPI UploadFile (images only — JPEG, PNG, WebP, GIF).
        category: Key from FOLDER_MAP that determines the Cloudinary folder.
                  Defaults to "general" → uploads/general.
        width:    Optional resize width (applied only when provided).
        height:   Optional resize height (applied only when provided).
        crop:     Cloudinary crop mode (default "limit" — never upscale).

    Returns:
        Cloudinary secure_url (HTTPS).
    """
    folder = FOLDER_MAP.get(category, FOLDER_MAP["general"])
    content = await _read_and_validate(file, "profile_photo")  # uses image-only validation

    transformation: list = []
    if width or height:
        t: dict = {"crop": crop}
        if width:
            t["width"] = width
        if height:
            t["height"] = height
        transformation.append(t)
    transformation += [{"quality": "auto:good"}, {"fetch_format": "auto"}]

    try:
        result = cloudinary.uploader.upload(
            content,
            folder=folder,
            resource_type="image",
            transformation=transformation,
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        return result["secure_url"]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"{category} image upload to Cloudinary failed: {exc}",
        )
