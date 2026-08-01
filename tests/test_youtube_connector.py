import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "backend"))

from app.connectors.youtube import (  # noqa: E402
    YouTubeTranscript,
    YouTubeTranscriptUnavailableError,
    YouTubeVideoUnavailableError,
    normalize_source_url,
)
from app.main import (  # noqa: E402
    YouTubeImportRequest,
    import_youtube_transcript,
    search_documents,
)
from app.models import Document  # noqa: E402


class YouTubeConnectorTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        return Session(self.engine)

    def test_successful_import_stores_document_and_is_searchable(self):
        transcript = YouTubeTranscript(
            video_id="abc123xyz",
            source_url=normalize_source_url("abc123xyz"),
            filename="abc123xyz",
            text_content="Atlas transcript keyword",
        )

        with self.get_session() as session:
            with patch("app.main.download_transcript", return_value=transcript):
                response = import_youtube_transcript(
                    YouTubeImportRequest(url="https://youtu.be/abc123xyz"),
                    session,
                )

            document = response["document"]
            self.assertEqual(response["status"], "saved")
            self.assertEqual(document.filename, "abc123xyz")
            self.assertEqual(document.file_type, "youtube")
            self.assertEqual(document.file_path, "")
            self.assertEqual(document.source_url, "https://youtu.be/abc123xyz")
            self.assertEqual(document.text_content, "Atlas transcript keyword")

            search_results = search_documents("keyword", session)
            self.assertEqual(len(search_results), 1)
            self.assertEqual(search_results[0].id, document.id)

    def test_invalid_url_returns_400(self):
        with self.get_session() as session:
            with self.assertRaises(HTTPException) as exc:
                import_youtube_transcript(
                    YouTubeImportRequest(url="https://example.com/video"),
                    session,
                )

        self.assertEqual(exc.exception.status_code, 400)

    def test_unsupported_youtube_subdomain_returns_400(self):
        with self.get_session() as session:
            with self.assertRaises(HTTPException) as exc:
                import_youtube_transcript(
                    YouTubeImportRequest(url="https://studio.youtube.com/video/abc123xyz"),
                    session,
                )

        self.assertEqual(exc.exception.status_code, 400)

    def test_duplicate_import_returns_409(self):
        with self.get_session() as session:
            session.add(
                Document(
                    filename="abc123xyz",
                    file_type="youtube",
                    file_path="",
                    source_url="https://youtu.be/abc123xyz",
                    text_content="Already imported",
                )
            )
            session.commit()

            with patch("app.main.download_transcript") as download_transcript:
                with self.assertRaises(HTTPException) as exc:
                    import_youtube_transcript(
                        YouTubeImportRequest(
                            url="https://www.youtube.com/watch?v=abc123xyz"
                        ),
                        session,
                    )

            self.assertEqual(exc.exception.status_code, 409)
            download_transcript.assert_not_called()

    def test_video_unavailable_returns_404(self):
        with self.get_session() as session:
            with patch(
                "app.main.download_transcript",
                side_effect=YouTubeVideoUnavailableError(
                    "YouTube video is unavailable"
                ),
            ):
                with self.assertRaises(HTTPException) as exc:
                    import_youtube_transcript(
                        YouTubeImportRequest(url="https://youtu.be/abc123xyz"),
                        session,
                    )

        self.assertEqual(exc.exception.status_code, 404)

    def test_transcript_unavailable_returns_422(self):
        with self.get_session() as session:
            with patch(
                "app.main.download_transcript",
                side_effect=YouTubeTranscriptUnavailableError(
                    "Transcript is unavailable for this YouTube video"
                ),
            ):
                with self.assertRaises(HTTPException) as exc:
                    import_youtube_transcript(
                        YouTubeImportRequest(url="https://youtu.be/abc123xyz"),
                        session,
                    )

        self.assertEqual(exc.exception.status_code, 422)

    def test_unexpected_error_returns_500(self):
        with self.get_session() as session:
            with patch(
                "app.main.download_transcript",
                side_effect=RuntimeError("Unexpected failure"),
            ):
                with self.assertRaises(HTTPException) as exc:
                    import_youtube_transcript(
                        YouTubeImportRequest(url="https://youtu.be/abc123xyz"),
                        session,
                    )

        self.assertEqual(exc.exception.status_code, 500)


if __name__ == "__main__":
    unittest.main()
