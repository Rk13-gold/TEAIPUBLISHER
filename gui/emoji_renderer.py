from pathlib import Path
import urllib.request
import threading

from PySide6.QtGui import QPixmap, QImage, QColor

from PIL import Image, ImageFont, ImageDraw

_FONT_PATH = Path('/usr/share/fonts/google-noto-emoji-fonts/NotoEmoji-Regular.ttf')
_CACHE_DIR = Path.home() / '.cache' / 'telegram-ai-emoji'
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE: dict[str, QPixmap] = {}
_CACHE_LOCK = threading.Lock()
_DOWNLOADING: set[str] = set()

_PIL_FONTS: dict[int, ImageFont.FreeTypeFont] = {}
if _FONT_PATH.exists():
    try:
        _PIL_FONTS[28] = ImageFont.truetype(str(_FONT_PATH), 28)
    except Exception:
        pass


def _codepoints(char: str) -> str:
    cps = []
    for c in char:
        o = ord(c)
        if o in (0xFE0F, 0x200D):
            continue
        cps.append(f'{o:x}')
    return '-'.join(cps)


def _local_path(char: str) -> Path:
    return _CACHE_DIR / f'{_codepoints(char)}.png'


def _render_pil(char: str, size: int) -> QPixmap | None:
    if not _FONT_PATH.exists():
        return None
    try:
        if size not in _PIL_FONTS:
            _PIL_FONTS[size] = ImageFont.truetype(str(_FONT_PATH), size)
        font = _PIL_FONTS[size]
        # Centrado preciso del glifo: el bbox del font recorta la porción de la
        # emoji; dibujamos compensando el offset para que no quede cortado.
        bbox = font.getbbox(char)
        if bbox:
            w = bbox[2] - bbox[0] + 4
            h = bbox[3] - bbox[1] + 4
        else:
            w = h = size
        img = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2 - bbox[0] if bbox else 2, 2 - bbox[1] if bbox else 2), char, font=font, fill=(255, 255, 255, 255))
        img = img.resize((size, size), Image.LANCZOS)
        qimg = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimg)
    except Exception:
        return None


def render_emoji(char: str, size: int = 28) -> QPixmap:
    with _CACHE_LOCK:
        if char in _CACHE:
            return _CACHE[char]

    # 1) Local cached PNG (from previous CDN download) — fast
    local = _local_path(char)
    if local.exists():
        pix = QPixmap(str(local))
        if not pix.isNull():
            if pix.width() != size or pix.height() != size:
                pix = pix.scaled(size, size)
            with _CACHE_LOCK:
                _CACHE[char] = pix
            return pix

    # 2) PIL monochrome rendering — fast, no network
    pix = _render_pil(char, size)
    if pix is not None:
        with _CACHE_LOCK:
            _CACHE[char] = pix
        # Kick off background download for next time
        threading.Thread(target=_download_twemoji, args=(char,), daemon=True).start()
        return pix

    fallback = QPixmap(size, size)
    fallback.fill(QColor(0, 0, 0, 0))
    with _CACHE_LOCK:
        _CACHE[char] = fallback
    return fallback


def _download_twemoji(char: str) -> None:
    """Download color emoji PNG in background thread. Result is cached on disk
    and the in-memory cache is invalidated so the next render is in color."""
    local = _local_path(char)
    if local.exists():
        return
    cp = _codepoints(char)
    url = f'https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/{cp}.png'
    with _CACHE_LOCK:
        if char in _DOWNLOADING:
            return
        _DOWNLOADING.add(char)
    try:
        req = urllib.request.Request(
            url, headers={'User-Agent': 'TelegramAIPublisher/1.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            local.write_bytes(data)
            # Drop cached monochrome so next render picks the color PNG
            with _CACHE_LOCK:
                _CACHE.pop(char, None)
    except Exception:
        pass
    finally:
        with _CACHE_LOCK:
            _DOWNLOADING.discard(char)


def prewarm(char: str, size: int = 28) -> None:
    """Encolar la descarga de un emoji en background para que esté en color
    cuando el usuario lo abra (evita el primer render monocromo)."""
    if _local_path(char).exists():
        return
    with _CACHE_LOCK:
        in_mem = char in _CACHE
    if not in_mem:
        render_emoji(char, size)
    if _local_path(char).exists():
        return
    threading.Thread(target=_download_twemoji, args=(char,), daemon=True).start()