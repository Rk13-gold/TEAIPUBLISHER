import re

ALLOWED_TAGS = {'b', 'i', 'u', 's', 'a', 'code', 'pre', 'strong', 'em', 'ins', 'del'}


def _escape(text: str) -> str:
    """Escape HTML special characters, but preserve allowed tags."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _clean_html(text: str) -> str:
    """Remove disallowed HTML tags, keep only Telegram-allowed ones."""
    def _repl(m):
        full = m.group(0)
        inner = m.group(1).lower().split()[0].rstrip('/')
        if inner in ALLOWED_TAGS or inner.startswith('/'):
            return full
        return ''
    return re.sub(r'</?(\w+(?:\s+\w+(?:\s*=\s*"[^"]*"|\'[^\']*\')?)*)\s*/?>', _repl, text, flags=re.DOTALL)


def prepare_content_for_telegram(content: str) -> str:
    """Convert raw editor text to Telegram-compatible HTML."""
    # Convert **bold** to <b>bold</b>
    content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
    # Convert *italic* to <i>italic</i>
    content = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', content)
    # Convert __underline__ to <u>underline</u>
    content = re.sub(r'__(.+?)__', r'<u>\1</u>', content)
    # Convert ~~strikethrough~~ to <s>strikethrough</s>
    content = re.sub(r'~~(.+?)~~', r'<s>\1</s>', content)
    # Convert ```code``` to <code>code</code>
    content = re.sub(r'```(.+?)```', r'<code>\1</code>', content)
    # Convert URLs to clickable links
    content = re.sub(
        r'(?<!<a href=")(https?://\S+)(?!">)',
        r'<a href="\1">\1</a>',
        content
    )
    # Normalize line breaks: <br> → \n
    content = content.replace('<br>', '\n')
    content = content.replace('<br/>', '\n')
    content = content.replace('<br />', '\n')
    # Clean unsafe HTML
    content = _clean_html(content)
    return content.strip()


def format_telegram_text(text: str) -> str:
    """Apply full Telegram formatting: detect titles, subtitles, lists, etc."""
    lines = text.splitlines()
    formatted = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted.append('')
            continue
        # Title (first line or ALL CAPS short text)
        if (stripped.isupper() and len(stripped) > 2 and len(stripped) < 60) or (
            formatted and not formatted[-1].startswith('<') and stripped == stripped.upper() and len(stripped) > 3
        ):
            formatted.append(f'<b>{stripped}</b>')
            continue
        # Lines starting with - or * become bullet points
        if stripped.startswith('- ') or stripped.startswith('* '):
            formatted.append(f'• {stripped[2:]}')
            continue
        # Numbered lists (1. 2. etc.)
        if re.match(r'^\d+\.\s', stripped):
            formatted.append(stripped)
            continue
        # URL detection
        if re.search(r'https?://\S+', stripped):
            stripped = re.sub(
                r'(https?://\S+)',
                r'<a href="\1">\1</a>',
                stripped
            )
            formatted.append(stripped)
            continue
        formatted.append(stripped)
    return '\n'.join(formatted)


def build_post_content(title: str, body: str, cta: str = '', hashtags: str = '') -> str:
    """Build the final post content as Telegram HTML."""
    parts = []
    if title:
        parts.append(f'<b>{title}</b>')
    if body:
        parts.append(body)
    footer_parts = []
    if cta:
        footer_parts.append(cta)
    if hashtags:
        footer_parts.append(hashtags)
    if footer_parts:
        parts.append('\n'.join(footer_parts))
    return '\n\n'.join(parts)
