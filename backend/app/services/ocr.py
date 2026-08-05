import logging
import time
from pathlib import Path


logger = logging.getLogger(__name__)


class OCRExtractionError(RuntimeError):
    pass


def extract_text_from_image(file_path: str) -> str:
    path = Path(file_path)
    start_time = time.perf_counter()

    logger.info("OCR started for %s", path)

    try:
        import pytesseract
        from PIL import Image, UnidentifiedImageError

        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

        with Image.open(path) as image:
            image = image.convert("L")   # grayscale
            text = pytesseract.image_to_string(image)
    except ImportError as exc:
        logger.exception("OCR dependencies are not installed")
        raise OCRExtractionError("OCR dependencies are not installed") from exc
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise

    text = text.strip()
    processing_time = time.perf_counter() - start_time

    logger.info("OCR completed for %s", path)
    logger.info("Characters extracted: %s", len(text))
    logger.info("OCR processing time: %.3f seconds", processing_time)

    return text
