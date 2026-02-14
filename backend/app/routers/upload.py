import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.report import Report
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.report import ReportResponse, UploadResponse
from app.utils.rate_limiter import check_upload_rate_limit
from app.utils.sanitization import sanitize_content_type, sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["uploads"])

UPLOAD_DIR = Path("/app/uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/dicom": ".dcm",
    "application/octet-stream": ".dcm",  # DICOM files often come as octet-stream
}

# Magic bytes for file type verification
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG"
_DICOM_MAGIC = b"DICM"


def _verify_file_magic(contents: bytes, claimed_type: str) -> bool:
    """Verify the file's magic bytes match the claimed content type."""
    if len(contents) < 4:
        return False

    if contents[:3] == _JPEG_MAGIC:
        return claimed_type == "image/jpeg"
    if contents[:4] == _PNG_MAGIC:
        return claimed_type == "image/png"
    # DICOM has a 128-byte preamble before the "DICM" marker
    if len(contents) > 132 and contents[128:132] == _DICOM_MAGIC:
        return claimed_type in ("application/dicom", "application/octet-stream")

    # If no known magic matched and type is octet-stream, allow (DICOM without standard preamble)
    if claimed_type == "application/octet-stream":
        return True

    return False


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Rate limiting: 5 uploads per hour per user
    check_upload_rate_limit(current_user.id)

    # Sanitize and validate content type
    content_type = sanitize_content_type(file.content_type)
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Accepted: JPEG, PNG, DICOM. Got: {content_type}",
        )

    # Sanitize filename for logging only (we generate our own storage name)
    original_filename = sanitize_filename(file.filename or "upload")
    logger.info(
        "Upload request from user %s: filename=%s, content_type=%s",
        current_user.id, original_filename, content_type,
    )

    # Read and validate size
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is 10MB. Got: {len(contents) / (1024 * 1024):.1f}MB",
        )

    # Verify file magic bytes match claimed type
    if not _verify_file_magic(contents, content_type):
        logger.warning(
            "File magic bytes do not match claimed type %s for user %s",
            content_type, current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match the declared file type.",
        )

    # Save file with a safe generated name
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = ALLOWED_TYPES[content_type]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as f:
        f.write(contents)

    logger.info("File saved: %s (%d bytes)", filename, len(contents))

    # Create report record
    image_url = f"/uploads/{filename}"
    report = Report(
        user_id=current_user.id,
        status="uploaded",
        image_url=image_url,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    logger.info("Report created: %s for user %s", report.id, current_user.id)
    return UploadResponse.model_validate(report)


@router.get("/reports", response_model=list[ReportResponse])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return [ReportResponse.model_validate(r) for r in reports]
