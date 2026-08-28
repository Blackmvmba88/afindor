from __future__ import annotations

import sys

import numpy as np

from blackmamba_tuner.music import frequency_to_note
from blackmamba_tuner.pitch import LibrosaPyinEngine


SAMPLE_RATE = 44_100
STANDARD_GUITAR = (
    ("E2", 82.4069),
    ("A2", 110.0000),
    ("D3", 146.8324),
    ("G3", 196.0000),
    ("B3", 246.9417),
    ("E4", 329.6276),
)


def synthetic_string(frequency_hz: float, duration: float = 0.25) -> np.ndarray:
    """Generate a deterministic guitar-like harmonic signal without microphone input."""
    sample_count = round(SAMPLE_RATE * duration)
    t = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE
    fundamental = 0.16 * np.sin(2.0 * np.pi * frequency_hz * t)
    second = 0.045 * np.sin(2.0 * np.pi * frequency_hz * 2.0 * t)
    third = 0.020 * np.sin(2.0 * np.pi * frequency_hz * 3.0 * t)
    envelope = np.exp(-1.4 * t)
    return np.asarray((fundamental + second + third) * envelope, dtype=np.float32)


def main() -> int:
    engine = LibrosaPyinEngine()
    failures = 0

    print("BlackMamba Tuner — DSP validation")
    print("=" * 72)

    for expected_note, expected_hz in STANDARD_GUITAR:
        result = engine.detect(synthetic_string(expected_hz), SAMPLE_RATE)
        if not result.voiced or result.frequency_hz is None:
            print(
                f"FAIL {expected_note:>2} {expected_hz:8.3f} Hz  "
                f"unvoiced  confidence={result.confidence:.3f}"
            )
            failures += 1
            continue

        reading = frequency_to_note(result.frequency_hz)
        frequency_error = result.frequency_hz - expected_hz
        passed = (
            reading.label == expected_note
            and abs(reading.cents) <= 5.0
            and result.confidence >= engine.min_confidence
        )
        state = "PASS" if passed else "FAIL"
        print(
            f"{state} {expected_note:>2} {expected_hz:8.3f} Hz -> "
            f"{result.frequency_hz:8.3f} Hz  "
            f"error={frequency_error:+7.3f} Hz  "
            f"cents={reading.cents:+6.2f}  conf={result.confidence:.3f}"
        )
        failures += int(not passed)

    print("=" * 72)
    if failures:
        print(f"DSP validation failed: {failures} string(s) outside tolerance")
        return 1

    print("DSP validation passed: all six standard guitar strings are inside tolerance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
