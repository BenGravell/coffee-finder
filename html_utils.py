from html import escape


def tag_wrap(text: str, tag: str) -> str:
    return f"<{tag}>{escape(text)}</{tag}>"


def anchor_wrap(text: str, url: str) -> str:
    return f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(text)}</a>'
