from __future__ import annotations

from dataclasses import dataclass
from math import log2

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


@dataclass(frozen=True, slots=True)
class NoteReading:
    name: str
    octave: int
    midi: int
    target_hz: float
    cents: float

    @property
    def label(self) -> str:
        return f"{self.name}{self.octave}"


def frequency_to_note(frequency_hz: float, a4_hz: float = 440.0) -> NoteReading:
    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive")
    if a4_hz <= 0:
        raise ValueError("a4_hz must be positive")

    midi_float = 69.0 + 12.0 * log2(frequency_hz / a4_hz)
    midi = round(midi_float)
    target_hz = a4_hz * (2.0 ** ((midi - 69) / 12.0))
    cents = 1200.0 * log2(frequency_hz / target_hz)

    return NoteReading(
        name=NOTE_NAMES[midi % 12],
        octave=(midi // 12) - 1,
        midi=midi,
        target_hz=target_hz,
        cents=cents,
    )
