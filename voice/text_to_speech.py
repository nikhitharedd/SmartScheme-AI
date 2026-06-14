import asyncio
import logging
from typing import Optional

import edge_tts

logger = logging.getLogger(__name__)

_LANGUAGE_VOICE_MAP: dict[str, list[str]] = {
    "en": ["en-US-GuyNeural", "en-IN-PriyaNeural"],
    "te": ["te-IN-ShrutiNeural"],
    "hi": ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"],
}

_DEFAULT_VOICES: dict[str, str] = {
    "en": "en-US-GuyNeural",
    "te": "te-IN-ShrutiNeural",
    "hi": "hi-IN-SwaraNeural",
}


class TextToSpeech:
    def __init__(self) -> None:
        self._voice_cache: Optional[list[dict]] = None

    def synthesize(
        self, text: str, language: str = "en", voice: Optional[str] = None
    ) -> bytes:
        if not text:
            raise ValueError("Text cannot be empty")

        selected_voice = voice or _DEFAULT_VOICES.get(language)
        if selected_voice is None:
            selected_voice = _DEFAULT_VOICES["en"]
            logger.warning(
                "No voice mapping for language '%s'; falling back to '%s'.",
                language,
                selected_voice,
            )

        try:
            data = asyncio.run(self._run_synthesize(text, selected_voice))
            return data
        except Exception as exc:
            logger.exception("TTS synthesis failed")
            raise RuntimeError(f"TTS synthesis error: {exc}") from exc

    async def _run_synthesize(self, text: str, voice: str) -> bytes:
        communicate = edge_tts.Communicate(text, voice)
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    def synthesize_file(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> str:
        audio_bytes = self.synthesize(text, language=language, voice=voice)
        try:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info("TTS audio written to '%s'", output_path)
        except OSError as exc:
            logger.exception("Failed to write TTS output to '%s'", output_path)
            raise RuntimeError(f"Could not write audio file: {exc}") from exc
        return output_path

    def get_available_voices(self, language: Optional[str] = None) -> list[dict]:
        if self._voice_cache is not None:
            voices = self._voice_cache
        else:
            try:
                voices = asyncio.run(self._fetch_voices())
                self._voice_cache = voices
            except Exception as exc:
                logger.exception("Failed to fetch voice list")
                raise RuntimeError(f"Could not retrieve voices: {exc}") from exc

        if language:
            return [v for v in voices if v.get("Locale", "").startswith(language)]
        return list(voices)

    @staticmethod
    async def _fetch_voices() -> list[dict]:
        voices = await edge_tts.list_voices()
        result: list[dict] = []
        for v in voices:
            result.append({
                "name": v.get("ShortName", v.get("Name", "")),
                "locale": v.get("Locale", ""),
                "gender": v.get("Gender", ""),
                "display_name": v.get("DisplayName", ""),
            })
        return result

    @staticmethod
    def get_language_voice_map() -> dict[str, list[str]]:
        return {k: list(v) for k, v in _LANGUAGE_VOICE_MAP.items()}

    @staticmethod
    def is_available() -> bool:
        try:
            asyncio.run(edge_tts.list_voices())
            return True
        except Exception:
            return False
