def tag_wrap(text: str, tag: str) -> str:
    return f"<{tag}>{text}</{tag}>"


def anchor_wrap(text: str, url: str) -> str:
    return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'
