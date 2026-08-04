import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from collections.abc import Generator
from typing import Any, Mapping

from dotenv import load_dotenv


logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[3]
SYSTEM_PROMPT = """You are Atlas Lite, a private AI knowledge assistant.

Answer ONLY using the supplied context.

Do not invent facts.

If the answer cannot be found inside the provided context, explicitly say:

'I couldn't find this information in your knowledge base.'

Keep answers concise, factual and cite the relevant sources."""


class GroqConfigurationError(RuntimeError):
    pass


class GroqServiceError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _get_groq_client() -> Any:
    load_dotenv(ROOT_DIR / ".env")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqConfigurationError("GROQ_API_KEY is not configured")

    from groq import Groq

    return Groq(api_key=api_key)


def _get_model() -> str:
    load_dotenv(ROOT_DIR / ".env")

    model = os.getenv("GROQ_MODEL")
    if not model:
        raise GroqConfigurationError("GROQ_MODEL is not configured")

    return model


def generate_chat_completion(
    messages: list[Mapping[str, str]],
    temperature: float = 0.2,
) -> str:
    client = _get_groq_client()
    model = _get_model()
    started_at = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
    except Exception as exc:
        logger.exception("Groq request failed")
        raise GroqServiceError("Groq request failed") from exc
    finally:
        latency_ms = (time.perf_counter() - started_at) * 1000
        logger.info("Groq response latency: %.2f ms", latency_ms)

    try:
        answer = response.choices[0].message.content
    except (AttributeError, IndexError) as exc:
        logger.exception("Groq response did not include an answer")
        raise GroqServiceError("Groq response did not include an answer") from exc

    return answer.strip() if answer else ""


def generate_answer(
    question: str,
    context: str,
    conversation_history: list[Mapping[str, str]] | None = None,
) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        messages.append(
            {
                "role": "user",
                "content": (
                    "Recent conversation history:\n"
                    f"{_format_conversation_history(conversation_history)}"
                ),
            }
        )

    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:\n{question}",
        }
    )

    return generate_chat_completion(messages, temperature=0.2)


def generate_answer_stream(
    question: str,
    context: str,
    conversation_history: list[Mapping[str, str]] | None = None,
) -> Generator[str, None, None]:
    client = _get_groq_client()
    model = _get_model()
    started_at = time.perf_counter()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        messages.append(
            {
                "role": "user",
                "content": (
                    "Recent conversation history:\n"
                    f"{_format_conversation_history(conversation_history)}"
                ),
            }
        )

    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:\n{question}",
        }
    )

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            stream=True,
        )

        for chunk in stream:
            try:
                content = chunk.choices[0].delta.content
            except (AttributeError, IndexError) as exc:
                logger.exception("Groq response did not include an answer")
                raise GroqServiceError(
                    "Groq response did not include an answer"
                ) from exc

            if content:
                yield content
    except GroqServiceError:
        raise
    except Exception as exc:
        logger.exception("Groq request failed")
        raise GroqServiceError("Groq request failed") from exc
    finally:
        latency_ms = (time.perf_counter() - started_at) * 1000
        logger.info("Groq response latency: %.2f ms", latency_ms)


def _format_conversation_history(
    conversation_history: list[Mapping[str, str]],
) -> str:
    formatted_messages: list[str] = []

    for message in conversation_history:
        role = message.get("role", "user").strip() or "user"
        content = message.get("content", "").strip()
        if not content:
            continue

        formatted_messages.append(f"{role}: {content}")

    return "\n".join(formatted_messages)
