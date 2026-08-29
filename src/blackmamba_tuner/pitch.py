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
    """Realtime pitch detector backed by librosa's probabilistic YIN.

    The defaults are tuned for chromatic guitar work. A 4096-sample frame is
    intentional: smaller frames are faster but materially reduce pYIN confidence
    around low E2/A2. We bound analysis to two recent frames so CPU and latency
    remain predictable without sacrificing the low strings.
    """

    def __init__(
        self,
        fmin: float = 60.0,
        fmax: float = 1_200.0,
        frame_length: int = 4_096,
        hop_length: int = 512,
        min_rms: float = 0.0025,
        min_confidence: float = 0.55,
    ) -> None:
        if fmin <= 0 or fmax <= fmin:
            raise ValueError("pitch range must satisfy 0 < fmin < fmax")
        if frame_length <= 0 or hop_length <= 0:
            raise ValueError("frame_length and hop_length must be positive")
        if hop_length > frame_length:
            raise ValueError("hop_length must be <= frame_length")

        self.fmin = fmin
        self.fmax = fmax
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.min_rms = min_rms
        self.min_confidence = min_confidence

    @staticmethod
    def _select_observed_frequency(frequencies: np.ndarray) -> float:
        """Pick a stable observed pitch without averaging across note changes.

        pYIN can return frames from two strings while the analysis window spans a
        transition. A raw median of an even split would average the two middle
        values and create a frequency that was never observed. We instead choose
        the dominant chromatic-note cluster, prefer the most recent cluster on a
        tie, then choose an observed frame nearest that cluster's median.
        """
        midi_bins = np.rint(69.0 + 12.0 * np.log2(frequencies / 440.0)).astype(np.int16)
        unique_bins, counts = np.unique(midi_bins, return_counts=True)
        max_count = int(np.max(counts))
        candidate_bins = set(int(value) for value in unique_bins[counts == max_count])

        selected_bin = next(
            int(value) for value in reversed(midi_bins) if int(value) in candidate_bins
        )
        cluster = frequencies[midi_bins == selected_bin]
        cluster_median = float(np.median(cluster))
        distances = np.abs(cluster - cluster_median)
        nearest = np.flatnonzero(np.isclose(distances, np.min(distances), rtol=0.0, atol=1e-12))
        return float(cluster[int(nearest[-1])])

    def detect(self, samples: np.ndarray, sample_rate: int) -> PitchResult:
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.fmax >= sample_rate / 2:
            raise ValueError("fmax must be below the Nyquist frequency")
        if samples.size < self.frame_length:
            return PitchResult(None, 0.0, 0.0, False)

        y = np.asarray(samples, dtype=np.float32)
        y = y - float(np.mean(y))
        rms = float(np.sqrt(np.mean(np.square(y), dtype=np.float64)))
        if rms < self.min_rms:
            return PitchResult(None, 0.0, rms, False)

        analysis_size = min(y.size, self.frame_length * 2)
        y = np.ascontiguousarray(y[-analysis_size:])

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

        frequency = self._select_observed_frequency(frequencies)
        return PitchResult(frequency, confidence, rms, True)
