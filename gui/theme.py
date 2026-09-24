"""Design tokens compartidos para toda la aplicación.

Una fuente única de verdad para colores, espaciado, radios y tamaños de
fuente. Los widgets de alto nivel (pickers, diálogos, previews) leen de
aquí en vez de repetir HEX brutos, para que el rediseño quede consistente.
"""

# --- Paleta base (dark) ---
BG_DEEP = "#000000"          # fondo de ventana/editor
SURFACE = "#0a0a0a"          # superficies elevadas (groupboxes, panes)
SURFACE_ALT = "#111111"      # campos de entrada / areas de búsqueda
SURFACE_RAISED = "#1a1a1a"   # cabeceras, listas
HOVER = "#202030"            # hover sobre superficies
ACTIVE = "#2d2f52"           # hover con tono de acento

# --- Acento (violeta, marca de la app) ---
ACCENT = "#7c5cfc"
ACCENT_HOVER = "#9178ff"
ACCENT_ACTIVE = "#5e3df0"
ACCENT_TEXT = "#c4b5fd"       # texto/aclaración con tono acento
ACCENT_SOFT = "rgba(124,92,252,0.14)"

# --- Texto ---
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#9aa0b0"
TEXT_MUTED = "#6c7086"
TEXT_ON_ACCENT = "#ffffff"

# --- Bordes ---
BORDER = "#333333"
BORDER_STRONG = "#45475a"

# --- Estado ---
SUCCESS = "#4ade80"
WARNING = "#fbbf24"
DANGER = "#f87171"
INFO = "#89b4fa"

# --- Escala de espaciado (px) ---
SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16}

# --- Radios (px) ---
RADIUS = {"sm": 4, "md": 6, "lg": 8, "xl": 12}

# --- Tipografía (px) ---
FONT = {"xs": 10, "sm": 11, "md": 13, "lg": 16, "xl": 20}


def rgba(hex_color: str, alpha: float) -> str:
    """Convierte `#rrggbb` a `rgba(r,g,b,a)` para QSS."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def emoji_button_qss() -> str:
    """QSS compartido para botones de emoji (botones cuadrados con icono)."""
    return f"""
        QPushButton {{
            background: transparent;
            border: 1px solid {BORDER};
            border-radius: {RADIUS['md']}px;
            padding: 2px;
        }}
        QPushButton:hover {{
            background: {ACTIVE};
            border: 1px solid {ACCENT};
        }}
        QPushButton:pressed {{
            background: {rgba(ACCENT, 0.35)};
        }}
    """