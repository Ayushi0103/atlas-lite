# Atlas Lite

# Atlas Lite

Atlas Lite is a personal knowledge management backend built with FastAPI.

It helps store, organize, search, and manage notes through a REST API. The project is being developed step by step to learn backend development while building the foundation for a future AI-powered knowledge management system.

The long-term goal is to make Atlas Lite capable of understanding and searching different types of information such as notes, PDFs, images, audio, and videos using natural language.

---

## Current Features

- Create notes
- List all notes
- Retrieve a note by ID
- Update notes
- Delete notes
- Keyword search
- Tags support
- Automatic timestamps
- SQLite persistence
- Alembic database migrations

---

## Tech Stack

- Python
- FastAPI
- SQLModel
- SQLite
- Alembic
- Pydantic

---

## Project Status

Atlas Lite is under active development.

Current focus:

- Build a production-ready backend
- Design a scalable database architecture
- Implement clean REST APIs
- Learn backend engineering best practices

Future roadmap includes:

- Authentication
- Advanced filtering and pagination
- AI-powered semantic search
- PDF and document indexing
- Image and audio support
- Vector database integration
- Natural language querying

---

## Vision

Atlas Lite is being developed as a personal knowledge engine that will eventually allow users to search and interact with their information using natural language.

The long-term objective is to create an intelligent layer that can organize, connect, and retrieve knowledge from multiple data sources while keeping user data private and under their control.

---

## Development

This repository is built incrementally using feature branches and sprint-based development, with each feature being designed, tested, and merged following a production-style workflow. 

---

## Supported Upload Types

Atlas Lite can ingest uploaded files as searchable documents.

- TXT
- PDF
- DOCX
- Markdown
- Images with OCR (`png`, `jpg`, `jpeg`, `webp`)
- Audio with Whisper (`mp3`, `wav`, `m4a`, `flac`, `ogg`)

Uploaded files are saved through the shared `/documents` endpoint, converted into
text, summarized, enriched with keywords, key concepts, and suggested questions,
embedded, indexed for semantic search, and made available to RAG chat.

---

## YouTube Connector

Atlas Lite can import a YouTube transcript as a normal searchable document.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
alembic upgrade head
```

Import a transcript:

```http
POST /connectors/youtube
Content-Type: application/json

{
  "url": "https://youtu.be/abc123xyz"
}
```

Example response:

```json
{
  "status": "saved",
  "document": {
    "id": 1,
    "filename": "abc123xyz",
    "file_type": "youtube",
    "file_path": "",
    "source_url": "https://youtu.be/abc123xyz",
    "text_content": "Full transcript text...",
    "created_at": "2026-08-01T10:00:00",
    "updated_at": "2026-08-01T10:00:00"
  }
}
```

Search imported transcripts with the existing document search endpoint:

```http
GET /documents/search?q=transcript
```

Notes:

- Only `youtube.com` and `youtu.be` URLs are accepted.
- Duplicate video imports return `409 Conflict`.
- Videos without available transcripts return `422 Unprocessable Entity`.

---

## OCR Image Ingestion

Atlas Lite can upload images and convert readable text into normal searchable
documents.

Supported image formats:

- `png`
- `jpg`
- `jpeg`
- `webp`

OCR workflow:

```text
Image upload
OCR extraction
Create Document
Save extracted text as text_content
Generate AI summary
Generate embeddings
Search through RAG
```

The image upload uses the same `/documents` endpoint as TXT, MD, PDF, and DOCX
files:

```http
POST /documents
Content-Type: multipart/form-data
```

Dependencies:

- `Pillow` opens and validates image files.
- `pytesseract` sends images to the Tesseract OCR engine.
- The Tesseract executable must be installed on the host system and available
  on `PATH`.

If OCR cannot extract readable text, Atlas Lite returns `400 Bad Request` with:

```text
Could not extract readable text from image.
```

---

## Audio Transcription Ingestion

Atlas Lite can upload audio files and convert speech into normal searchable
documents using Faster Whisper.

Supported audio formats:

- `mp3`
- `wav`
- `m4a`
- `flac`
- `ogg`

Audio workflow:

```text
Audio upload
Whisper transcription
Create Document
Save transcript as text_content
Generate AI summary
Generate keywords, key concepts, and suggested questions
Generate embeddings
Index for semantic search
Search through RAG
```

The audio upload uses the same `/documents` endpoint as TXT, MD, PDF, DOCX, and
image files:

```http
POST /documents
Content-Type: multipart/form-data
```

Dependencies:

- `faster-whisper` runs speech-to-text transcription.
- `ctranslate2` provides the inference runtime used by Faster Whisper.
- The Whisper model is loaded lazily in CPU mode and cached after the first
  audio upload.

If transcription fails or produces no readable speech, Atlas Lite returns
`400 Bad Request` with a meaningful error message.
