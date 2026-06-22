from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


class UploadValidationError(ValidationError):
    pass


def validate_pdf_upload(uploaded_file) -> None:
    max_bytes = getattr(settings, "MAX_PDF_UPLOAD_BYTES", 10 * 1024 * 1024)
    if uploaded_file.size > max_bytes:
        raise UploadValidationError(
            f"PDF exceeds maximum size of {max_bytes // (1024 * 1024)}MB."
        )
    if not uploaded_file.name.lower().endswith(".pdf"):
        raise UploadValidationError("Only PDF files are allowed for booking import.")

    uploaded_file.seek(0)
    header = uploaded_file.read(5)
    uploaded_file.seek(0)
    if not header.startswith(b"%PDF"):
        raise UploadValidationError("Uploaded file is not a valid PDF.")


def validate_image_upload(uploaded_file) -> None:
    max_bytes = getattr(settings, "MAX_IMAGE_UPLOAD_BYTES", 5 * 1024 * 1024)
    if uploaded_file.size > max_bytes:
        raise UploadValidationError(
            f"Image exceeds maximum size of {max_bytes // (1024 * 1024)}MB."
        )

    content_type = getattr(uploaded_file, "content_type", "") or ""
    allowed = getattr(
        settings,
        "ALLOWED_IMAGE_CONTENT_TYPES",
        {"image/jpeg", "image/png", "image/webp", "image/gif"},
    )
    if content_type and content_type not in allowed:
        raise UploadValidationError(f"Unsupported image type: {content_type}")

    uploaded_file.seek(0)
    try:
        with Image.open(uploaded_file) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise UploadValidationError("Uploaded file is not a valid image.") from exc
    finally:
        uploaded_file.seek(0)
