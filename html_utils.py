"""Utilities for interacting with HTML."""


def tag_wrap(text: str, tag: str) -> str:
    """Wrap text with a tag."""
    return f"<{tag}>{text}</{tag}>"


def anchor_wrap(text: str, url: str) -> str:
    """Wrap text with a URL anchor."""
    return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'
