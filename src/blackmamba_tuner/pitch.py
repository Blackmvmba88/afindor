from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import librosa
import numpy as np


@dataclass(frozen=True, slots=True)
class PitchResult:
    frequency_hz: float | None
    confidence: float
    rms: float
    voiced: bool


class PitchEngine(Protocol):
    def detect(self, samples: np.ndarray, sample_rate: int) -> PitchResult: ...


class LibrosaPyinEngine:
    """Pitch detector backed by librosa's probabilistic YIN implementation."""

    def __init__(
        self,
        fmin: float = 60.0,
        fmax: float = 1_200.0,
        frame_length: int = 4_096,
        hop_length: int = 512,
        min_rms: float = 0.0025,
        min_confidence: float = 0.55,
    ) -> None:
        self.fmin = fmin
        self.fmax = fmax
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.min_rms = min_rms
        self.min_confidence = min_confidence

    def detect(self, samples: np.ndarray, sample_rate: int) -> PitchResult:
        if samples.size < self.frame_length:
            return PitchResult(None, 0.0, 0.0, False)

        y = np.asarray(samples, dtype=np.float32)
        y = y - float(np.mean(y))
        rms = float(np.sqrt(np.mean(np.square(y), dtype=np.float64)))
        if rms < self.min_rms:
            return PitchResult(None, 0.0, rms, False)

        # Work on a bounded recent window so latency/CPU usage stay predictable.
        analysis_size = min(y.size, self.frame_length * 2)
        y = y[-analysis_size:]

        f0, voiced_flag, voiced_prob = librosa.pyin(
            y,
            fmin=self.fmin,
            fmax=self.fmax,
            sr=sample_rate,
            frame_length=self.frame_length,
            hop_length=self.hop_length,
            center=False,
        )

        if f0 is None or voiced_flag is None or voiced_prob is None:
            return PitchResult(None, 0.0, rms, False)

        valid = voiced_flag & np.isfinite(f0) & np.isfinite(voiced_prob)
        if not np.any(valid):
            return PitchResult(None, 0.0, rms, False)

        frequencies = np.asarray(f0[valid], dtype=np.float64)
        probabilities = np.asarray(voiced_prob[valid], dtype=np.float64)
        confidence = float(np.median(probabilities))

        if confidence < self.min_confidence:
            return PitchResult(None, confidence, rms, False)

        # Probability-weighted mean is less jumpy than taking a single frame.
        frequency = float(np.average(frequencies, weights=np.maximum(probabilities, 1e-6)))
        return PitchResult(frequency, confidence, rms, True)
