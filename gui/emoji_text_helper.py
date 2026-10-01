from PySide6.QtGui import QTextImageFormat, QTextDocument, QTextCursor, QImage
from PySide6.QtCore import QUrl
from gui.emoji_renderer import render_emoji


def _emoji_name(char: str) -> str:
    cps = []
    for c in char:
        o = ord(c)
        if o not in (0xFE0F, 0x200D):
            cps.append(f'{o:x}')
    return f'emoji_{"-".join(cps)}'


def _calc_size(textedit, size: int | None) -> int:
    if size is not None:
        return size
    font = textedit.font()
    ps = font.pixelSize()
    if ps > 0:
        return max(12, min(ps, 20))
    pts = font.pointSize()
    if pts > 0:
        return max(12, min(pts, 20))
    return 14


def _insert_emoji_qtextedit(textedit, emoji: str, size: int):
    """Insert emoji as an inline rendered image at the cursor position."""
    pix = render_emoji(emoji, size)
    if pix is None or pix.isNull():
        cursor = textedit.textCursor()
        cursor.insertText(emoji)
        return
    name = _emoji_name(emoji)
    doc = textedit.document()
    resource = doc.resource(QTextDocument.ImageResource, QUrl(name))
    if resource is None:
        img = pix.toImage()
        doc.addResource(QTextDocument.ImageResource, QUrl(name), img)
    fmt = QTextImageFormat()
    fmt.setName(name)
    fmt.setWidth(pix.width())
    fmt.setHeight(pix.height())
    cursor = textedit.textCursor()
    cursor.insertImage(fmt)


def insert_emoji_textedit(textedit, emoji: str, size: int = None):
    _insert_emoji_qtextedit(textedit, emoji, _calc_size(textedit, size))


def emoji_document_to_plaintext(doc: QTextDocument) -> str:
    """Extract text from a QTextDocument as Telegram-ready text.

    Emoji stored as inline images become plain characters again, bold/italic/
    underline runs become Telegram tags, and every line break the user typed
    is emitted as a single ``\\n`` so the editor, the preview and the published
    message all agree on the layout.
    """
    parts = []
    block = doc.begin()
    while block != doc.end():
        block_text = []
        it = block.begin()
        while it != block.end():
            frag = it.fragment()
            it += 1
            if frag is None or not frag.isValid():
                continue
            cf = frag.charFormat()
            if cf.isImageFormat():
                name = cf.toImageFormat().name()
                if name.startswith('emoji_'):
                    block_text.append(_emoji_name_to_chars(name))
                continue
            text = frag.text()
            if not text:
                continue
            if cf.fontWeight() >= 700:
                text = f'<b>{text}</b>'
            if cf.fontItalic():
                text = f'<i>{text}</i>'
            if cf.fontUnderline():
                text = f'<u>{text}</u>'
            block_text.append(text)

        text = ''.join(block_text)
        # A soft line break (Shift+Enter) is stored as U+2028 inside the block.
        if '\u2028' in text:
            text = text.replace('\u2028', '\n')
        else:
            # Otherwise this block ends with a hard break, except for the first.
            if parts:
                parts.append('\n')
        parts.append(text)
        block = block.next()

    return ''.join(parts)


def _emoji_name_to_chars(name: str) -> str:
    """Turn an ``emoji_<hex>-<hex>`` resource name back into its characters."""
    try:
        return ''.join(chr(int(cp, 16)) for cp in name[len('emoji_'):].split('-'))
    except ValueError:
        return ''
