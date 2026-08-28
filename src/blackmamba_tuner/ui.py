from __future__ import annotations

from collections import deque

import numpy as np
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from .audio import AudioInput
from .music import frequency_to_note
from .pitch import LibrosaPyinEngine, PitchResult
from .settings import SettingsStore
from .themes import THEMES, Theme, build_stylesheet, get_theme


class CentsMeter(QWidget):
    def __init__(self, theme: Theme) -> None:
        super().__init__()
        self._cents = 0.0
        self._theme = theme
        self.setMinimumHeight(150)

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def set_cents(self, cents: float) -> None:
        self._cents = max(-50.0, min(50.0, cents))
        self.update()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(24, 24, -24, -24)
        center_x = rect.center().x()
        baseline = rect.bottom() - 12
        half_width = rect.width() / 2

        painter.setPen(QPen(QColor(self._theme.border), 2))
        painter.drawLine(rect.left(), baseline, rect.right(), baseline)

        painter.setPen(QPen(QColor(self._theme.muted), 2))
        for cents in (-50, -25, 0, 25, 50):
            x = center_x + (cents / 50.0) * half_width
            tick_height = 26 if cents == 0 else 14
            painter.drawLine(int(x), baseline - tick_height, int(x), baseline + 4)
            painter.drawText(int(x - 14), baseline + 24, 28, 20, Qt.AlignCenter, str(cents))

        x = center_x + (self._cents / 50.0) * half_width
        in_tune = abs(self._cents) <= 3.0
        needle_color = self._theme.in_tune if in_tune else self._theme.warning
        painter.setPen(QPen(QColor(needle_color), 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(int(x), rect.top(), int(x), baseline - 8)


class PitchWorker(QThread):
    detected = Signal(object)
    failed = Signal(str)

    def __init__(self, audio: AudioInput, engine: LibrosaPyinEngine) -> None:
        super().__init__()
        self.audio = audio
        self.engine = engine

    def run(self) -> None:
        while not self.isInterruptionRequested():
            try:
                result = self.engine.detect(self.audio.snapshot(), self.audio.sample_rate)
                self.detected.emit(result)
            except Exception as exc:  # keep audio/UI alive and surface the problem
                self.failed.emit(str(exc))

            if self.isInterruptionRequested():
                break
            self.msleep(45)

    def stop(self) -> None:
        # Never let Python/Qt destroy a live QThread. The first librosa/Numba
        # analysis can take longer than a fixed timeout while JIT warms up.
        self.requestInterruption()
        self.wait()


class TunerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BlackMamba Tuner")
        self.resize(680, 580)

        self.settings = SettingsStore()
        self.theme = get_theme(self.settings.theme_key)
        self.audio = AudioInput()
        self.engine = LibrosaPyinEngine()
        self.worker: PitchWorker | None = None
        self._cents_history: deque[float] = deque(maxlen=5)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(32, 24, 32, 28)
        layout.setSpacing(18)

        header = QHBoxLayout()
        brand_label = QLabel("BLACKMAMBA TUNER")
        brand_label.setFont(QFont("Arial", 14, QFont.Bold))
        header.addWidget(brand_label)
        header.addStretch(1)

        theme_label = QLabel("Theme")
        theme_label.setObjectName("mutedLabel")
        header.addWidget(theme_label)

        self.theme_combo = QComboBox()
        for key, theme in THEMES.items():
            self.theme_combo.addItem(theme.name, key)
        current_index = self.theme_combo.findData(self.theme.key)
        self.theme_combo.setCurrentIndex(max(0, current_index))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        header.addWidget(self.theme_combo)

        self.note_label = QLabel("—")
        self.note_label.setAlignment(Qt.AlignCenter)
        self.note_label.setFont(QFont("Arial", 76, QFont.Bold))

        self.frequency_label = QLabel("Play a string")
        self.frequency_label.setAlignment(Qt.AlignCenter)
        self.frequency_label.setFont(QFont("Arial", 18))

        self.cents_label = QLabel("0.0 cents")
        self.cents_label.setAlignment(Qt.AlignCenter)

        self.meter = CentsMeter(self.theme)

        confidence_row = QHBoxLayout()
        confidence_label = QLabel("Confidence")
        confidence_label.setObjectName("mutedLabel")
        confidence_row.addWidget(confidence_label)
        self.confidence = QProgressBar()
        self.confidence.setRange(0, 100)
        self.confidence.setValue(0)
        self.confidence.setTextVisible(True)
        confidence_row.addWidget(self.confidence, 1)

        self.status_label = QLabel("Stopped")
        self.status_label.setObjectName("mutedLabel")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.toggle_button = QPushButton("Start tuner")
        self.toggle_button.setObjectName("primaryButton")
        self.toggle_button.setMinimumHeight(48)
        self.toggle_button.clicked.connect(self.toggle)

        layout.addLayout(header)
        layout.addWidget(self.note_label)
        layout.addWidget(self.frequency_label)
        layout.addWidget(self.cents_label)
        layout.addWidget(self.meter)
        layout.addLayout(confidence_row)
        layout.addWidget(self.status_label)
        layout.addWidget(self.toggle_button)

        self.setCentralWidget(root)
        self._apply_theme(self.theme)

    def _apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.setStyleSheet(build_stylesheet(theme))
        self.meter.set_theme(theme)

    def _on_theme_changed(self) -> None:
        key = str(self.theme_combo.currentData())
        self.settings.theme_key = key
        self._apply_theme(get_theme(key))

    def toggle(self) -> None:
        if self.worker is None:
            self.start_tuner()
        else:
            self.stop_tuner()

    @staticmethod
    def _friendly_audio_error(exc: Exception) -> str:
        message = str(exc)
        lowered = message.lower()
        if "permission" in lowered or "not permitted" in lowered:
            return "Microphone permission required — grant it once in macOS Privacy & Security"
        return f"Audio error: {message}"

    def start_tuner(self) -> None:
        if self.worker is not None:
            return

        self.status_label.setText("Opening microphone…")
        try:
            self.audio.start()
        except Exception as exc:
            self.status_label.setText(self._friendly_audio_error(exc))
            return

        worker = PitchWorker(self.audio, self.engine)
        worker.detected.connect(self.on_pitch)
        worker.failed.connect(self._on_worker_error)
        self.worker = worker
        worker.start()
        self.status_label.setText("Listening…")
        self.toggle_button.setText("Stop tuner")

    def stop_tuner(self) -> None:
        worker = self.worker
        if worker is not None:
            worker.stop()
            self.worker = None

        self.audio.stop()
        self._cents_history.clear()
        self.confidence.setValue(0)
        self.status_label.setText("Stopped")
        self.toggle_button.setText("Start tuner")

    def _on_worker_error(self, message: str) -> None:
        self.status_label.setText(f"DSP error: {message}")

    def on_pitch(self, result: PitchResult) -> None:
        self.confidence.setValue(round(result.confidence * 100))

        if not result.voiced or result.frequency_hz is None:
            self.status_label.setText("Listening…")
            return

        reading = frequency_to_note(result.frequency_hz)
        self._cents_history.append(reading.cents)
        smoothed_cents = float(np.median(self._cents_history))

        self.note_label.setText(reading.label)
        self.frequency_label.setText(
            f"{result.frequency_hz:.2f} Hz  •  target {reading.target_hz:.2f} Hz"
        )
        self.cents_label.setText(f"{smoothed_cents:+.1f} cents")
        self.meter.set_cents(smoothed_cents)

        if abs(smoothed_cents) <= 3.0:
            state = "IN TUNE"
        elif smoothed_cents < 0:
            state = "FLAT — tune up"
        else:
            state = "SHARP — tune down"
        self.status_label.setText(state)

    def closeEvent(self, event) -> None:
        self.stop_tuner()
        event.accept()
