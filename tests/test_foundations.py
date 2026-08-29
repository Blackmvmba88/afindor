import numpy as np
import pytest

from blackmamba_tuner.audio import AudioInput
from blackmamba_tuner.pitch import LibrosaPyinEngine
from blackmamba_tuner.themes import DEFAULT_THEME, THEMES, get_theme


def test_audio_configuration_rejects_invalid_sizes() -> None:
    with pytest.raises(ValueError):
        AudioInput(sample_rate=0)
    with pytest.raises(ValueError):
        AudioInput(block_size=0)
    with pytest.raises(ValueError):
        AudioInput(block_size=1024, window_size=512)


def test_audio_ring_buffer_keeps_latest_samples_in_order() -> None:
    audio = AudioInput(block_size=4, window_size=8)

    audio._callback(np.array([[1], [2], [3], [4]], dtype=np.float32), 4, None, None)
    audio._callback(np.array([[5], [6], [7], [8]], dtype=np.float32), 4, None, None)
    audio._callback(np.array([[9], [10], [11], [12]], dtype=np.float32), 4, None, None)

    np.testing.assert_array_equal(
        audio.snapshot(),
        np.array([5, 6, 7, 8, 9, 10, 11, 12], dtype=np.float32),
    )


def test_unknown_theme_falls_back_to_default() -> None:
    assert get_theme("does-not-exist") == THEMES[DEFAULT_THEME]


def test_all_themes_have_unique_keys() -> None:
    assert {theme.key for theme in THEMES.values()} == set(THEMES)


def test_pitch_engine_rejects_invalid_ranges() -> None:
    with pytest.raises(ValueError):
        LibrosaPyinEngine(fmin=100.0, fmax=100.0)
    with pytest.raises(ValueError):
        LibrosaPyinEngine(frame_length=512, hop_length=1024)


def test_silence_is_not_reported_as_a_note() -> None:
    engine = LibrosaPyinEngine()
    result = engine.detect(np.zeros(8192, dtype=np.float32), 44_100)
    assert result.voiced is False
    assert result.frequency_hz is None
    assert result.confidence == 0.0


def test_pitch_transition_selects_an_observed_frequency(monkeypatch) -> None:
    observed = np.array([82.0, 82.2, 110.0, 110.2], dtype=np.float64)

    def fake_pyin(*args, **kwargs):
        del args, kwargs
        return (
            observed,
            np.ones(observed.size, dtype=bool),
            np.full(observed.size, 0.9, dtype=np.float64),
        )

    monkeypatch.setattr("blackmamba_tuner.pitch.librosa.pyin", fake_pyin)
    engine = LibrosaPyinEngine(frame_length=4, hop_length=1, min_rms=0.0)
    samples = np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0], dtype=np.float32)

    result = engine.detect(samples, 44_100)

    assert result.voiced is True
    assert result.frequency_hz in observed
    assert result.frequency_hz >= 110.0
