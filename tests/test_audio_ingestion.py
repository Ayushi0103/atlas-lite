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


class AudioIngestionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        return Session(self.engine)

    def make_upload(self, filename: str) -> UploadFile:
        return UploadFile(filename=filename, file=BytesIO(b"audio bytes"))

    def test_audio_extraction_uses_transcription_service(self):
        audio_path = APP_ROOT_DIR / "uploads" / "lecture.mp3"

        with patch("app.main.transcribe_audio", return_value="Lecture transcript"):
            text = extract_text_from_document(audio_path, "mp3")

        self.assertEqual(text, "Lecture transcript")

    def test_empty_transcription_output_returns_400(self):
        saved_path = APP_ROOT_DIR / "uploads" / "empty.mp3"

        with self.get_session() as session:
            with patch("app.main.save_upload_file", return_value=saved_path):
                with patch("app.main.transcribe_audio", return_value="   "):
                    with self.assertRaises(HTTPException) as exc:
                        upload_document(session, self.make_upload("empty.mp3"))

        self.assertEqual(exc.exception.status_code, 400)
        self.assertEqual(
            exc.exception.detail,
            "Could not extract readable speech from audio.",
        )

    def test_audio_upload_creates_searchable_document(self):
        saved_path = APP_ROOT_DIR / "uploads" / "lecture.mp3"

        with self.get_session() as session:
            with patch("app.main.save_upload_file", return_value=saved_path):
                with patch(
                    "app.main.transcribe_audio",
                    return_value="Atlas audio keyword",
                ):
                    with patch("app.main.safely_index_document") as index_document:
                        with patch("app.main.safely_summarize_document") as summarize:
                            response = upload_document(
                                session,
                                self.make_upload("lecture.mp3"),
                            )

            document = response["document"]
            self.assertEqual(response["status"], "saved")
            self.assertEqual(document.filename, "lecture.mp3")
            self.assertEqual(document.file_type, "mp3")
            self.assertEqual(document.text_content, "Atlas audio keyword")
            index_document.assert_not_called()
            summarize.assert_called_once_with(document, session)

    def test_unsupported_audio_extension_returns_400(self):
        with self.get_session() as session:
            with self.assertRaises(HTTPException) as exc:
                upload_document(session, self.make_upload("lecture.aac"))

        self.assertEqual(exc.exception.status_code, 400)
        self.assertIn("Unsupported file type", exc.exception.detail)


if __name__ == "__main__":
    unittest.main()
