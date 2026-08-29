import pytest

from blackmamba_tuner.music import frequency_to_note


def test_a4_is_exactly_440_hz() -> None:
    reading = frequency_to_note(440.0)
    assert reading.label == "A4"
    assert reading.target_hz == pytest.approx(440.0)
    assert reading.cents == pytest.approx(0.0, abs=1e-9)


def test_low_e_guitar_string_maps_to_e2() -> None:
    reading = frequency_to_note(82.4069)
    assert reading.label == "E2"
    assert reading.cents == pytest.approx(0.0, abs=0.01)


def test_positive_cents_means_sharp() -> None:
    reading = frequency_to_note(445.0)
    assert reading.label == "A4"
    assert reading.cents > 0


def test_invalid_frequency_is_rejected() -> None:
    with pytest.raises(ValueError):
        frequency_to_note(0.0)
