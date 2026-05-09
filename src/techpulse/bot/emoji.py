"""Branded TechPulse custom Telegram emoji.

Each entry pairs a `custom_emoji_id` from the @techpulse emoji pack with a
unicode fallback. Premium clients render the branded sticker; non-Premium
clients fall back to the unicode glyph embedded in the tag, so messages stay
readable everywhere.

Use `tg_emoji(name)` inline in HTML-formatted messages.
"""

from html import escape

_EMOJI: dict[str, tuple[str, str]] = {
    "logo":        ("5188236243489562083", "\U0001F493"),  # pink heartbeat
    "youtube":     ("5474158895058427917", "▶️"),  # play button
    "github":      ("5474400203500985839", "\U0001F332"),  # evergreen tree
    "interests":   ("5474245193836307455", "✳️"),  # asterisk
    "digest":      ("5474574312885229879", "\U0001F49A"),  # green heart
    "ai":          ("5188353934183408412", "⚡"),       # high voltage
    "success":     ("5474164624544799511", "✅"),       # check mark
    "error":       ("5474509471763963926", "❌"),       # cross mark
    "loading":     ("5188406440158600825", "⏳"),       # hourglass
    "help":        ("5474256700053692091", "\U0001F431"),  # cat face
    "heart_pink":  ("5474423258885431751", "\U0001FA77"),  # pink heart
    "heart_green": ("5474260406610466510", "\U0001F49A"),  # green heart
}


def tg_emoji(name: str) -> str:
    """Render a custom emoji as an HTML `<tg-emoji>` tag with unicode fallback."""
    emoji_id, fallback = _EMOJI[name]
    return f'<tg-emoji emoji-id="{emoji_id}">{escape(fallback)}</tg-emoji>'
