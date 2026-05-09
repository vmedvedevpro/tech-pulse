import hashlib
from typing import Final

import anthropic
from loguru import logger

_NATIVE_LANG: Final = "en"

_PROMPT_TEMPLATE: Final = (
    "Translate the following Telegram bot message into {lang_name}. "
    "Preserve every HTML tag and every <tg-emoji ...>...</tg-emoji> tag exactly as written, "
    "including their attributes and inner content. Keep slash-commands like /help unchanged. "
    "Do not add commentary, explanations, or surrounding quotes — output ONLY the translated text.\n\n"
    "Message:\n{text}"
)

_LANG_NAMES: Final[dict[str, str]] = {
    "ru": "Russian",
    "uk": "Ukrainian",
    "be": "Belarusian",
    "es": "Spanish",
    "pt": "Portuguese",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pl": "Polish",
    "tr": "Turkish",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "id": "Indonesian",
    "vi": "Vietnamese",
    "nl": "Dutch",
    "cs": "Czech",
    "sv": "Swedish",
    "no": "Norwegian",
    "fi": "Finnish",
    "da": "Danish",
    "el": "Greek",
    "he": "Hebrew",
    "th": "Thai",
    "kk": "Kazakh",
    "uz": "Uzbek",
}


class Localizer:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._cache: dict[tuple[str, str], str] = {}

    async def localize(self, text: str, lang_code: str | None) -> str:
        target = self._resolve_lang(lang_code)
        if target is None:
            return text

        key = (self._fingerprint(text), target)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        translated = await self._translate(text, target)
        self._cache[key] = translated
        return translated

    @staticmethod
    def _resolve_lang(lang_code: str | None) -> str | None:
        if not lang_code:
            return None
        primary = lang_code.split("-")[0].lower()
        if primary == _NATIVE_LANG:
            return None
        return _LANG_NAMES.get(primary)

    @staticmethod
    def _fingerprint(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    async def _translate(self, text: str, lang_name: str) -> str:
        prompt = _PROMPT_TEMPLATE.format(lang_name=lang_name, text=text)
        try:
            message = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            logger.warning("localizer api error | lang={} | {}", lang_name, exc)
            return text
        parts = [block.text for block in message.content if isinstance(block, anthropic.types.TextBlock)]
        return "".join(parts).strip() or text
