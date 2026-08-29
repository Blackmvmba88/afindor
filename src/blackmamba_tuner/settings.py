from __future__ import annotations

from PySide6.QtCore import QSettings

from .themes import DEFAULT_THEME, THEMES


class SettingsStore:
    """Small typed wrapper around QSettings.

    Qt stores preferences in the native platform settings location. Keeping the
    organization/application identity stable means preferences survive upgrades
    without inventing our own config format.
    """

    THEME_KEY = "appearance/theme"

    def __init__(self) -> None:
        self._settings = QSettings()

    @property
    def theme_key(self) -> str:
        value = str(self._settings.value(self.THEME_KEY, DEFAULT_THEME))
        return value if value in THEMES else DEFAULT_THEME

    @theme_key.setter
    def theme_key(self, value: str) -> None:
        self._settings.setValue(
            self.THEME_KEY,
            value if value in THEMES else DEFAULT_THEME,
        )
        self._settings.sync()
