import logging
import time
from functools import lru_cache
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

WHISPER_MODEL_NAME = "base"


class AudioTranscriptionError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_whisper_model() -> Any:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        logger.exception("Faster Whisper dependencies are not installed")
        raise AudioTranscriptionError(
            "Audio transcription dependencies are not installed"
        ) from exc

    model = WhisperModel(WHISPER_MODEL_NAME, device="cpu", compute_type="int8")
    logger.info("Whisper model loaded: %s", WHISPER_MODEL_NAME)
    return model


def transcribe_audio(file_path: str) -> str:
    path = Path(file_path)
    start_time = time.perf_counter()

    logger.info("Transcription started for %s", path)

    try:
        _validate_audio_file(path)
        model = get_whisper_model()
        segments, _ = model.transcribe(str(path))
        text = " ".join(segment.text.strip() for segment in segments).strip()

        if not text:
            raise AudioTranscriptionError(
                "No speech could be extracted from the audio."
            )
    except AudioTranscriptionError:
        raise
    except Exception as exc:
        logger.exception("Audio transcription failed for %s", path)
        raise AudioTranscriptionError("Could not transcribe audio file") from exc

    processing_time = time.perf_counter() - start_time

    logger.info("Transcription completed for %s", path)
    logger.info("Characters extracted: %s", len(text))
    logger.info("Transcription processing time: %.3f seconds", processing_time)

    return text


def _validate_audio_file(path: Path) -> None:
    if not path.exists():
        raise AudioTranscriptionError("Audio file does not exist")

    if not path.is_file():
        raise AudioTranscriptionError("Audio path is not a file")

    if path.stat().st_size == 0:
        raise AudioTranscriptionError("Audio file is empty")
