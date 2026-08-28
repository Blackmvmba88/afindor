from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Theme:
    key: str
    name: str
    background: str
    surface: str
    text: str
    muted: str
    accent: str
    accent_alt: str
    in_tune: str
    warning: str
    danger: str
    border: str


THEMES: dict[str, Theme] = {
    "mamba-gold": Theme(
        key="mamba-gold",
        name="Mamba Gold",
        background="#080909",
        surface="#111311",
        text="#F5F1E6",
        muted="#9D9D93",
        accent="#D6B34C",
        accent_alt="#F0D978",
        in_tune="#57E389",
        warning="#F6B94A",
        danger="#FF5C6C",
        border="#2A2E29",
    ),
    "venom": Theme(
        key="venom",
        name="Venom",
        background="#050A08",
        surface="#0C1511",
        text="#E9FFF4",
        muted="#7FA98F",
        accent="#56F58B",
        accent_alt="#52D9FF",
        in_tune="#70FF9F",
        warning="#FFE05B",
        danger="#FF667A",
        border="#173326",
    ),
    "crimson": Theme(
        key="crimson",
        name="Crimson",
        background="#0C0708",
        surface="#180D10",
        text="#FFF0F2",
        muted="#B38C93",
        accent="#FF3B55",
        accent_alt="#FF8B64",
        in_tune="#62E6A2",
        warning="#FFC857",
        danger="#FF3B55",
        border="#3A1C24",
    ),
    "midnight": Theme(
        key="midnight",
        name="Midnight",
        background="#080A12",
        surface="#101522",
        text="#F0F3FF",
        muted="#8F98B8",
        accent="#8C7CFF",
        accent_alt="#55D6FF",
        in_tune="#59E6B3",
        warning="#FFCB66",
        danger="#FF6584",
        border="#252C44",
    ),
}

DEFAULT_THEME = "mamba-gold"


def get_theme(key: str) -> Theme:
    return THEMES.get(key, THEMES[DEFAULT_THEME])


def build_stylesheet(theme: Theme) -> str:
    return f"""
    QMainWindow, QWidget {{
        background-color: {theme.background};
        color: {theme.text};
    }}
    QLabel {{
        color: {theme.text};
        background: transparent;
    }}
    QLabel#mutedLabel {{
        color: {theme.muted};
    }}
    QPushButton, QComboBox {{
        color: {theme.text};
        background-color: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 10px;
        padding: 9px 14px;
    }}
    QPushButton:hover, QComboBox:hover {{
        border-color: {theme.accent};
    }}
    QPushButton#primaryButton {{
        color: {theme.background};
        background-color: {theme.accent};
        border-color: {theme.accent};
        font-weight: 700;
    }}
    QPushButton#primaryButton:hover {{
        background-color: {theme.accent_alt};
        border-color: {theme.accent_alt};
    }}
    QProgressBar {{
        color: {theme.text};
        background-color: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        text-align: center;
        min-height: 18px;
    }}
    QProgressBar::chunk {{
        background-color: {theme.accent};
        border-radius: 7px;
    }}
    """
