from __future__ import annotations

import threading

import numpy as np
import sounddevice as sd


class AudioInput:
    def __init__(
        self,
        sample_rate: int = 44_100,
        block_size: int = 1_024,
        window_size: int = 8_192,
        device: int | str | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.window_size = window_size
        self.device = device

        self._buffer = np.zeros(window_size, dtype=np.float32)
        self._write_index = 0
        self._filled = 0
        self._lock = threading.Lock()
        self._stream: sd.InputStream | None = None

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        del frames, time_info, status
        mono = np.asarray(indata[:, 0], dtype=np.float32)
        if mono.size >= self.window_size:
            mono = mono[-self.window_size :]

        with self._lock:
            count = mono.size
            first = min(count, self.window_size - self._write_index)
            self._buffer[self._write_index : self._write_index + first] = mono[:first]
            remaining = count - first
            if remaining:
                self._buffer[:remaining] = mono[first:]

            self._write_index = (self._write_index + count) % self.window_size
            self._filled = min(self.window_size, self._filled + count)

    def start(self) -> None:
        if self._stream is not None:
            return

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            latency="low",
            device=self.device,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is None:
            return
        self._stream.stop()
        self._stream.close()
        self._stream = None

    def snapshot(self) -> np.ndarray:
        with self._lock:
            if self._filled == 0:
                return np.empty(0, dtype=np.float32)

            if self._filled < self.window_size:
                return self._buffer[: self._filled].copy()

            return np.concatenate(
                (
                    self._buffer[self._write_index :],
                    self._buffer[: self._write_index],
                )
            )
