"""OCR service – extracts raw text from images using Tesseract."""
from __future__ import annotations

import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _try_import_tesseract() -> bool:
    try:
        import pytesseract  # noqa: F401
        return True
    except ImportError:
        return False


def ocr_image_bytes(data: bytes, lang: str = "eng") -> str:
    """Run Tesseract OCR on raw image bytes and return the extracted text."""
    if not _try_import_tesseract():
        logger.warning("pytesseract not installed – skipping OCR")
        return ""

    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(data))
    text: str = pytesseract.image_to_string(image, lang=lang)
    return text.strip()


def ocr_image_path(path: str | Path, lang: str = "eng") -> str:
    """Run Tesseract OCR on an image file and return the extracted text."""
    return ocr_image_bytes(Path(path).read_bytes(), lang=lang)


def ocr_pdf_bytes(data: bytes, lang: str = "eng") -> str:
    """Render each page of a PDF to an image and OCR it.

    This is the fallback for PDFs that have no embedded text layer.
    """
    try:
        from pdf2image import convert_from_bytes
    except ImportError:
        logger.warning("pdf2image not installed – cannot OCR PDF pages")
        return ""

    if not _try_import_tesseract():
        return ""

    import pytesseract

    pages = convert_from_bytes(data, dpi=200)
    parts: list[str] = []
    for page in pages:
        parts.append(pytesseract.image_to_string(page, lang=lang).strip())
    return "\n\n".join(parts)
