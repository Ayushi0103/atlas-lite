import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from sqlmodel import Session, SQLModel, create_engine


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "backend"))

from app.main import (  # noqa: E402
    ROOT_DIR as APP_ROOT_DIR,
    extract_text_from_document,
    upload_document,
)


class OCRIngestionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        return Session(self.engine)

    def make_upload(self, filename: str) -> UploadFile:
        return UploadFile(filename=filename, file=BytesIO(b"image bytes"))

    def test_image_extraction_uses_ocr_service(self):
        image_path = APP_ROOT_DIR / "uploads" / "scan.png"

        with patch("app.main.extract_text_from_image", return_value="Receipt total"):
            text = extract_text_from_document(image_path, "png")

        self.assertEqual(text, "Receipt total")

    def test_empty_ocr_output_returns_400(self):
        saved_path = APP_ROOT_DIR / "uploads" / "empty.png"

        with self.get_session() as session:
            with patch("app.main.save_upload_file", return_value=saved_path):
                with patch("app.main.extract_text_from_image", return_value="   "):
                    with self.assertRaises(HTTPException) as exc:
                        upload_document(session, self.make_upload("empty.png"))

        self.assertEqual(exc.exception.status_code, 400)
        self.assertEqual(
            exc.exception.detail,
            "Could not extract readable text from image.",
        )

    def test_image_upload_creates_searchable_document(self):
        saved_path = APP_ROOT_DIR / "uploads" / "receipt.png"

        with self.get_session() as session:
            with patch("app.main.save_upload_file", return_value=saved_path):
                with patch("app.main.extract_text_from_image", return_value="Atlas OCR keyword"):
                    with patch("app.main.safely_index_document") as index_document:
                        with patch("app.main.safely_summarize_document") as summarize:
                            response = upload_document(
                                session,
                                self.make_upload("receipt.png"),
                            )

            document = response["document"]
            self.assertEqual(response["status"], "saved")
            self.assertEqual(document.filename, "receipt.png")
            self.assertEqual(document.file_type, "png")
            self.assertEqual(document.text_content, "Atlas OCR keyword")
            index_document.assert_not_called()
            summarize.assert_called_once_with(document, session)


if __name__ == "__main__":
    unittest.main()
