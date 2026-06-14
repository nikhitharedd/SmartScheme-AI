import logging
from typing import Optional

import faster_whisper

logger = logging.getLogger(__name__)

_LANGUAGE_MAP = {
    "telugu": "te",
    "tamil": "ta",
    "hindi": "hi",
    "english": "en",
    "bengali": "bn",
    "marathi": "mr",
    "gujarati": "gu",
    "urdu": "ur",
    "kannada": "kn",
    "malayalam": "ml",
    "odia": "or",
    "punjabi": "pa",
}

_SUPPORTED_LANGUAGES = ["en", "te", "hi", "ta", "bn", "mr", "gu", "ur", "kn", "ml", "or", "pa"]


class SpeechToText:
    def __init__(self, model_size: str = "base"):
        if model_size not in ("tiny", "base", "small", "medium", "large-v3"):
            raise ValueError(
                f"Invalid model_size '{model_size}'. "
                f"Options: tiny, base, small, medium, large-v3"
            )
        self._model_size: str = model_size
        self._model: Optional[faster_whisper.WhisperModel] = None

    def _ensure_model(self) -> faster_whisper.WhisperModel:
        if self._model is not None:
            return self._model
        try:
            logger.info("Loading faster-whisper model '%s' ...", self._model_size)
            self._model = faster_whisper.WhisperModel(self._model_size)
            logger.info("Model '%s' loaded successfully.", self._model_size)
        except Exception as exc:
            logger.exception("Failed to load model '%s'", self._model_size)
            raise RuntimeError(f"Could not load faster-whisper model: {exc}") from exc
        return self._model

    @staticmethod
    def _normalise_language(language: Optional[str]) -> Optional[str]:
        if language is None:
            return None
        lang = language.strip().lower().replace("_", "-")
        lang = _LANGUAGE_MAP.get(lang, lang)
        if len(lang) > 2:
            lang = lang.split("-")[0]
        return lang

    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> dict:
        model = self._ensure_model()
        lang = self._normalise_language(language)

        try:
            import io
            import soundfile as sf

            audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
            segments, info = model.transcribe(audio_array, language=lang, beam_size=5)
            detected_lang = info.language if lang is None else lang
            text_parts: list[str] = []
            segment_list: list[dict] = []
            for seg in segments:
                text_parts.append(seg.text)
                segment_list.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "confidence": getattr(seg, "avg_logprob", None),
                })
            return {
                "text": " ".join(text_parts).strip(),
                "language": detected_lang,
                "segments": segment_list,
            }
        except Exception as exc:
            logger.exception("Transcription failed")
            raise RuntimeError(f"Transcription error: {exc}") from exc

    def transcribe_file(self, filepath: str, language: Optional[str] = None) -> dict:
        model = self._ensure_model()
        lang = self._normalise_language(language)

        try:
            segments, info = model.transcribe(filepath, language=lang, beam_size=5)
            detected_lang = info.language if lang is None else lang
            text_parts: list[str] = []
            segment_list: list[dict] = []
            for seg in segments:
                text_parts.append(seg.text)
                segment_list.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "confidence": getattr(seg, "avg_logprob", None),
                })
            return {
                "text": " ".join(text_parts).strip(),
                "language": detected_lang,
                "segments": segment_list,
            }
        except FileNotFoundError:
            logger.error("Audio file not found: %s", filepath)
            raise
        except Exception as exc:
            logger.exception("Transcription failed for file '%s'", filepath)
            raise RuntimeError(f"Transcription error: {exc}") from exc

    def set_model_size(self, model_size: str) -> None:
        if model_size not in ("tiny", "base", "small", "medium", "large-v3"):
            raise ValueError(
                f"Invalid model_size '{model_size}'. "
                f"Options: tiny, base, small, medium, large-v3"
            )
        if model_size != self._model_size:
            self._model = None
            self._model_size = model_size
            logger.info("Model size set to '%s' (will load on next call).", model_size)

    @staticmethod
    def get_supported_languages() -> list[str]:
        return list(_SUPPORTED_LANGUAGES)

    def transcribe_streaming(
        self, audio_generator, language: Optional[str] = None
    ) -> dict:
        chunks: list[bytes] = []
        for chunk in audio_generator:
            chunks.append(chunk)
        full_audio = b"".join(chunks)
        return self.transcribe(full_audio, language=language)
