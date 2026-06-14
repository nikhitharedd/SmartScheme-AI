import json
from pathlib import Path
from threading import Lock


class I18nManager:
    _instance = None
    _lock = Lock()
    _initialized: bool = False
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, translations_dir: str = "translations"):
        if self._initialized:
            return
        self._initialized = True
        self._translations_dir = translations_dir
        self._current_lang = "en"
        self._translations: dict[str, dict[str, str]] = {}
        self._supported_languages = {
            "en": {"name": "English", "native_name": "English"},
            "te": {"name": "Telugu", "native_name": "తెలుగు"},
            "hi": {"name": "Hindi", "native_name": "हिन्दी"},
        }
        self.load_translations()

    @classmethod
    def get_instance(cls, translations_dir: str = "translations"):
        return cls(translations_dir)

    def set_language(self, lang: str) -> None:
        if lang not in self._supported_languages:
            allowed = list(self._supported_languages.keys())
            raise ValueError(f"Unsupported language '{lang}'. Allowed: {allowed}")
        self._current_lang = lang

    def get_language(self) -> str:
        return self._current_lang

    def t(self, key: str, **kwargs) -> str:
        lang = self._current_lang
        translations = self._translations.get(lang, {})
        fallback_en = self._translations.get("en", {})

        template = translations.get(key) or fallback_en.get(key) or key
        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError:
                return template
        return template

    def load_translations(self) -> dict:
        self._translations.clear()
        trans_path = Path(self._translations_dir)
        if not trans_path.exists():
            for lang_code in self._supported_languages:
                self._translations[lang_code] = {}
            return self._translations

        for file_path in trans_path.glob("*.json"):
            lang_code = file_path.stem
            if lang_code in self._supported_languages:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    data = {}
                self._translations[lang_code] = data

        for lang_code in self._supported_languages:
            if lang_code not in self._translations:
                self._translations[lang_code] = {}

        return self._translations

    def get_available_languages(self) -> list[dict]:
        result = []
        for code, info in self._supported_languages.items():
            result.append({
                "code": code,
                "name": info["name"],
                "native_name": info["native_name"],
            })
        return result

    def Reload(self) -> None:
        self._translations.clear()
        self.load_translations()
