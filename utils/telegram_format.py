"""Canonical Telegram text pipeline.

Single source of truth for every place that renders or publishes text:
the Publish tab editor, the AI generator editor and their live previews all
run through :func:`prepare_content_for_telegram`, so what the preview shows
is exactly what Telegram receives.

Output is Telegram "HTML" parse mode, restricted to the tag set documented at
https://core.telegram.org/bots/api#html-style

Line breaks are always plain ``\\n``.  Telegram counts lengths *after* entities
parsing, so this module clamps on the raw HTML length (always >= the parsed
length) to stay safe under either interpretation.
"""

import re

# --- Telegram Bot API limits -------------------------------------------------
TELEGRAM_TEXT_LIMIT = 4096      # sendMessage text, after entities parsing
TELEGRAM_CAPTION_LIMIT = 1024   # photo/video/animation/voice caption

# --- Telegram supported HTML tags (Bot API 10.3) ----------------------------
_TAG_ALIASES = {
    'b': 'b', 'strong': 'b',
    'i': 'i', 'em': 'i',
    'u': 'u', 'ins': 'u',
    's': 's', 'strike': 's', 'del': 's',
    'code': 'code',
    'pre': 'pre',
    'tg-spoiler': 'tg-spoiler',
    'span': 'span',
    'blockquote': 'blockquote',
    'a': 'a',
    'tg-emoji': 'tg-emoji',
    'tg-time': 'tg-time',
}
TELEGRAM_ALLOWED_TAGS = frozenset(_TAG_ALIASES)

_BLOCK_TAGS = frozenset({'pre', 'blockquote'})

# Telegram refuses links with any other scheme.
_SAFE_URL_SCHEMES = ('http://', 'https://', 'tg://')
# A valid custom emoji id is a decimal number (also reused for tg-time unix).
_EMOJI_ID_RE = re.compile(r'^\d{1,20}$')
# tg-time format: strftime-like letters; allow letters plus a few separators.
_FORMAT_RE = re.compile(r'^[\w\s%+\-,.:/\\]+$')
# Syntax-highlight language name for <pre><code class="language-...">.
_LANGUAGE_RE = re.compile(r'^[A-Za-z0-9_+#.-]{1,32}$')

_ENTITY_RE = re.compile(r'&(?:[a-zA-Z][a-zA-Z0-9]{1,10}|#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6});')
# Attributes may be quoted (``name="value"``) or bare (``expandable``).
_ATTR_PART = r'((?:\s+[\w-]+(?:\s*=\s*(?:"[^"]*"|\'[^\']*\'))?)*)'
_TAG_RE = re.compile(
    r'<(/?)([\w:][\w:.-]*)' + _ATTR_PART + r'\s*(/?)>'
)
_ATTR_RE = re.compile(r'([\w-]+)(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'))?')
_URL_RE = re.compile(r'(?:https?://|tg://)\S+')

_BULLET_RE = re.compile(r'^\s*[-*•]\s+')


def normalize_newlines(text: str) -> str:
    """Collapse every newline convention down to a single ``\\n``.

    Handles CRLF/CR pasted from Windows, the vertical tab and form feed that
    ``splitlines`` treats as breaks, and the Unicode line/paragraph separators
    Qt inserts for Shift+Enter.
    """
    if not text:
        return ''
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\u2028', '\n').replace('\u2029', '\n')
    text = text.replace('\u000b', '\n').replace('\u000c', '\n')
    text = text.replace('\u0085', '\n')
    return text


def escape_html(text: str) -> str:
    """Escape ``&``, ``<`` and ``>`` the way Telegram's HTML mode requires."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _escape_attr(value: str) -> str:
    return escape_html(value).replace('"', '&quot;')


def _canonical_tag(tag: str):
    return _TAG_ALIASES.get(tag.lower())


def _render_tag(match):
    """Rebuild a tag with a canonical name, or return ``None`` to drop it."""
    closing, raw_tag, attr_text, _self_closing = match.groups()
    canonical = _canonical_tag(raw_tag)
    if canonical is None:
        return None

    attrs = {}
    for name, dq, sq in _ATTR_RE.findall(attr_text or ''):
        # A bare attribute such as ``expandable`` maps to an empty string.
        attrs[name.lower()] = dq or sq or ''

    if closing:
        # <span class="tg-spoiler"> is normalized to <tg-spoiler> when opening,
        # so its closer has to be normalized the same way.
        if canonical == 'span':
            return '</tg-spoiler>'
        return f'</{canonical}>'
    if canonical == 'pre':
        return '<pre>'
    if canonical == 'blockquote':
        return '<blockquote expandable>' if 'expandable' in attrs else '<blockquote>'
    if canonical == 'a':
        href = attrs.get('href', '')
        if not href.lower().startswith(_SAFE_URL_SCHEMES):
            return None
        return f'<a href="{_escape_attr(href)}">'
    if canonical == 'tg-emoji':
        emoji_id = attrs.get('emoji-id', '')
        if not _EMOJI_ID_RE.match(emoji_id):
            return None
        return f'<tg-emoji emoji-id="{_escape_attr(emoji_id)}">'
    if canonical == 'tg-time':
        unix = attrs.get('unix', '')
        if not _EMOJI_ID_RE.match(unix):
            return None
        fmt = attrs.get('format', '')
        if fmt:
            if not _FORMAT_RE.match(fmt):
                return None
            return f'<tg-time unix="{_escape_attr(unix)}" format="{_escape_attr(fmt)}">'
        return f'<tg-time unix="{_escape_attr(unix)}">'
    if canonical == 'code':
        # Telegram only honours the syntax-highlight language class on <code>
        # inside <pre>. Anything else on <code> is dropped.
        lang = attrs.get('class', '').strip()
        if lang.startswith('language-'):
            lang = lang[len('language-'):]
            if _LANGUAGE_RE.match(lang):
                return f'<code class="language-{_escape_attr(lang)}">'
            return '<code>'
        return '<code>'
    if canonical == 'span':
        # Only Telegram's spoiler class is honoured; any other <span> is dropped.
        if 'tg-spoiler' not in attrs.get('class', '').split():
            return None
        return '<tg-spoiler>'
    return f'<{canonical}>'


def _protect_tags(text: str, store: list) -> str:
    """Replace supported Telegram tags with opaque placeholders.

    Anything that is not a supported tag is left in the text untouched, so it
    gets HTML-escaped afterwards: user input can never inject markup, and no
    word is ever swallowed by a stray angle bracket.

    Openers and closers are accepted as a unit. A closer is only kept when it
    matches the innermost open tag and that opener was renderable, so an
    unsupported opener keeps its own closer and nothing is left dangling.
    """
    matches = list(_TAG_RE.finditer(text))
    rejected = set()

    # Decide acceptance up front so a rejected opener also loses its closer.
    # A closer is only kept when it matches the innermost open tag; anything
    # else is a stray closer and gets dropped, which _repair_tags then
    # rebalances by closing the still-open tags in order.
    stack = []
    for match in matches:
        closing, raw_tag, _, _ = match.groups()
        canonical = _canonical_tag(raw_tag)
        if canonical is None:
            continue
        if closing:
            if stack and stack[-1][0] == canonical:
                if not stack[-1][1]:
                    rejected.add(match.start())
                stack.pop()
            else:
                rejected.add(match.start())
        else:
            stack.append((canonical, _render_tag(match) is not None))

    out = []
    pos = 0
    for match in matches:
        rendered = _render_tag(match)
        if rendered is None or match.start() in rejected:
            # Leave it in the stream so escaping turns it into visible text
            # instead of silently deleting the user's words.
            continue
        out.append(text[pos:match.start()])
        store.append(rendered)
        out.append(f'\x00{len(store) - 1}\x00')
        pos = match.end()
    out.append(text[pos:])
    return ''.join(out)


def _protect_links(text: str, store: list) -> str:
    """Turn bare URLs into placeholders so escaping cannot corrupt them."""
    out = []
    pos = 0
    for m in _URL_RE.finditer(text):
        url = m.group().rstrip('.,;:!?)\'"]')
        if not url:
            continue
        out.append(text[pos:m.start()])
        escaped = _escape_attr(url)
        store.append(f'<a href="{escaped}">{escaped}</a>')
        out.append(f'\x00{len(store) - 1}\x00')
        pos = m.start() + len(url)
    out.append(text[pos:])
    return ''.join(out)


def _apply_markdown(text: str) -> str:
    """Inline markdown -> Telegram HTML. Input must already be HTML-escaped."""

    def fenced(m):
        body = m.group('code').strip('\n')
        if not body:
            return ''
        lang = (m.groupdict().get('lang') or '').strip()
        if lang and _LANGUAGE_RE.match(lang):
            return f'<pre><code class="language-{_escape_attr(lang)}">{body}</code></pre>'
        return f'<pre><code>{body}</code></pre>'

    # Fenced block, optionally tagged with a language: ```python ... ```
    text = re.sub(
        r'```[ \t]*(?P<lang>[\w_+#.-]*)[ \t]*\n(?P<code>.*?)```',
        fenced, text, flags=re.DOTALL,
    )
    # Fenced block on a single line: ```code```
    text = re.sub(r'```(?P<code>[^\n`]+)```', fenced, text)
    text = re.sub(r'(?<!\w)`([^`\n]+)`(?!\w)', r'<code>\1</code>', text)

    text = re.sub(r'~~(?=\S)(.+?)(?<=\S)~~', r'<s>\1</s>', text, flags=re.DOTALL)
    text = re.sub(r'\*\*(?=\S)(.+?)(?<=\S)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(?=\S)(.+?)(?<=\S)__', r'<u>\1</u>', text, flags=re.DOTALL)
    text = re.sub(r'\*(?=\S)([^*\n]+?)(?<=\S)\*', r'<i>\1</i>', text)
    text = re.sub(r'(?<![\w\\])_(?=\S)([^_\n]+?)(?<=\S)_(?![\w])', r'<i>\1</i>', text)
    text = re.sub(r'\|\|(?=\S)(.+?)(?<=\S)\|\|', r'<tg-spoiler>\1</tg-spoiler>', text,
                  flags=re.DOTALL)

    return text


def _render_blockquotes(body: str) -> str:
    """Wrap runs of ``>`` lines into a single ``<blockquote>``."""
    out = []
    buf = []

    def flush():
        if buf:
            out.append('<blockquote>' + '\n'.join(buf) + '</blockquote>')
            buf.clear()

    for line in body.split('\n'):
        stripped = line.strip()
        if stripped.startswith('&gt;'):
            # At this point the line is already HTML-escaped, so a quote
            # marker shows up as the entity rather than a literal '>'.
            buf.append(stripped[4:].strip())
        else:
            flush()
            out.append(line)
    flush()
    return '\n'.join(out)


def _normalize_bullets(body: str) -> str:
    """Render ``-``/``*`` list markers as a bullet, the way the preview showed."""
    lines = []
    for line in body.split('\n'):
        stripped = line.lstrip()
        if not _BULLET_RE.match(stripped):
            lines.append(line)
            continue
        indent = line[:len(line) - len(stripped)]
        content = stripped.split(None, 1)[1] if len(stripped.split(None, 1)) > 1 else ''
        lines.append(f'{indent}\u2022 {content}'.rstrip())
    return '\n'.join(lines)


def prepare_content_for_telegram(content: str) -> str:
    """Convert raw editor text into Telegram-compatible HTML.

    Handles markdown shortcuts, HTML pasted by the user, autolinks and line
    breaks, and guarantees the result only contains tags Telegram accepts.
    """
    if not content:
        return ''

    text = normalize_newlines(content)
    # <br> in any spelling is a line break, not markup Telegram understands.
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    store = []
    text = _protect_tags(text, store)
    text = _protect_links(text, store)
    text = escape_html(text)
    text = _apply_markdown(text)

    text = re.sub(r'\x00(\d+)\x00', lambda m: store[int(m.group(1))], text)
    text = _normalize_bullets(text)
    text = _render_blockquotes(text)
    return _repair_tags(text).strip('\n')


# --- Tag balancing -----------------------------------------------------------

def _walk_tags(html: str, close_open: bool):
    """Run the tag stack over ``html``; returns (rendered, open_stack)."""
    out = []
    stack = []
    pos = 0
    for m in _TAG_RE.finditer(html):
        out.append(html[pos:m.start()])
        pos = m.end()
        closing, raw_tag, _, _ = m.groups()
        canonical = _canonical_tag(raw_tag)
        if canonical is None:
            continue
        if closing:
            if canonical in stack:
                while stack and stack[-1] != canonical:
                    out.append(f'</{stack.pop()}>')
                if stack:
                    stack.pop()
                out.append(f'</{canonical}>')
            # A closer without its opener is dropped.
        else:
            stack.append(canonical)
            # Emit verbatim so attributes such as href / emoji-id survive.
            out.append(m.group(0))
    out.append(html[pos:])
    if close_open:
        out.extend(f'</{t}>' for t in reversed(stack))
    return ''.join(out), stack


def _repair_tags(html: str) -> str:
    """Drop stray closing tags and close anything left open."""
    return _walk_tags(html, close_open=True)[0]


def open_tags_of(html: str) -> list:
    """Tags still open at the end of ``html`` (used when splitting)."""
    return _walk_tags(html, close_open=False)[1]


# --- Length handling ---------------------------------------------------------

def visible_length(html: str) -> int:
    """Length Telegram will show for ``html`` (tags excluded, entities resolved)."""
    text = _TAG_RE.sub('', html)
    for entity, char in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&quot;', '"')):
        text = text.replace(entity, char)
    text = _ENTITY_RE.sub('\ufffc', text)
    return len(text)


def _safe_prefix(text: str, max_len: int) -> str:
    """Longest prefix of ``text`` (len <= max_len) that is not mid-tag."""
    head = text[:max_len]
    if head.rfind('<') > head.rfind('>'):
        head = head[:head.rfind('<')]
    return _walk_tags(head, close_open=False)[0]


def clamp_telegram_text(html: str, limit: int = TELEGRAM_TEXT_LIMIT,
                        ellipsis: str = '\n\n...') -> str:
    """Trim ``html`` to at most ``limit`` characters with tags still valid.

    The closing tags are reserved from the budget first, so the result never
    exceeds ``limit`` -- Telegram rejects captions/text that do.
    """
    if len(html) <= limit:
        return html
    if limit <= 0:
        return ''
    if len(ellipsis) >= limit:
        return ellipsis[:limit]

    # Reserve room for the ellipsis plus the tags we are going to re-open.
    stack = open_tags_of(html[:max(0, limit - len(ellipsis))])
    reserved = len(ellipsis) + sum(len(f'</{t}>') for t in stack)

    head = _safe_prefix(html, max(0, limit - reserved))
    # Repair only balances tags; never let it push the result past the limit.
    repaired = _repair_tags(head.rstrip())
    if len(repaired) > limit - len(ellipsis):
        repaired = _safe_prefix(repaired, limit - len(ellipsis))
    return repaired + ellipsis


def split_telegram_text(html: str, limit: int = TELEGRAM_TEXT_LIMIT) -> list:
    """Split HTML into chunks Telegram accepts, one per returned element.

    Splits on ``\\n`` boundaries so paragraphs stay intact, and never cuts a tag
    in half.  When a single paragraph is still too long it is split on a hard
    boundary with the enclosing tags re-balanced.
    """
    if not html:
        return []
    if len(html) <= limit:
        return [_repair_tags(html)]

    chunks = []
    current = ''

    def flush():
        nonlocal current
        if current.strip():
            chunks.append(_repair_tags(current))
        current = ''

    for paragraph in html.split('\n'):
        candidate = paragraph if not current else current + '\n' + paragraph
        if current and len(candidate) > limit:
            flush()
            candidate = paragraph
        current = candidate
        while len(current) > limit:
            head, tail = _hard_split(current, limit)
            chunks.append(_repair_tags(head))
            current = tail
    flush()
    return chunks


def _hard_split(text: str, limit: int):
    """Cut ``text`` into (head, tail) where head + its closing tags fits limit."""
    stack = open_tags_of(text[:limit])
    closing = ''.join(f'</{t}>' for t in reversed(stack))
    head = _safe_prefix(text, max(1, limit - len(closing)))
    if not head:
        head = text[:1]
    return head, text[len(head):]


# --- Post assembly -----------------------------------------------------------

def build_post_content(title: str, body: str, cta: str = '', hashtags: str = '') -> str:
    """Assemble the final post as Telegram HTML.

    The title is bold, blocks are separated by a blank line (two ``\\n``), and
    the CTA/hashtag footer keeps the CTA and hashtags on consecutive lines.
    """
    parts = []
    if title:
        parts.append(f'<b>{escape_html(title.strip())}</b>')
    if body:
        parts.append(body)
    footer = []
    if cta:
        footer.append(prepare_content_for_telegram(cta.strip()))
    if hashtags:
        footer.append(prepare_content_for_telegram(hashtags.strip()))
    footer = [f for f in footer if f]
    if footer:
        parts.append('\n'.join(footer))
    return '\n\n'.join(parts)


def html_to_preview_html(html: str) -> str:
    """Convert canonical Telegram HTML into something Qt's HTML importer renders.

    Qt's HTML importer collapses whitespace, so every ``\\n`` becomes a
    ``<br/>``; the rest is already valid escaped Telegram HTML.
    """
    return html.replace('\n', '<br/>')


def compose_post_html(title: str, body: str, cta: str = '', hashtags: str = '') -> str:
    """The exact Telegram HTML for a post, ready for preview or for sending."""
    return build_post_content(title, body, cta, hashtags)
