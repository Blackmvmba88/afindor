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
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if block_size <= 0:
            raise ValueError("block_size must be positive")
        if window_size < block_size:
            raise ValueError("window_size must be >= block_size")

        self.sample_rate = sample_rate
        self.block_size = block_size
        self.window_size = window_size
        self.device = device

        self._buffer = np.zeros(window_size, dtype=np.float32)
        self._write_index = 0
        self._filled = 0
        self._lock = threading.Lock()
        self._stream: sd.InputStream | None = None
        self._last_status = ""

    @property
    def running(self) -> bool:
        stream = self._stream
        return bool(stream is not None and stream.active)

    @property
    def last_status(self) -> str:
        return self._last_status

    def _reset_buffer(self) -> None:
        with self._lock:
            self._buffer.fill(0.0)
            self._write_index = 0
            self._filled = 0

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        del frames, time_info
        if status:
            self._last_status = str(status)

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
        if self.running:
            return

        # Close a stale stream before creating a new one. This keeps repeated
        # Start/Stop cycles deterministic and avoids leaking CoreAudio handles.
        self.stop()
        self._reset_buffer()
        self._last_status = ""

        sd.check_input_settings(
            device=self.device,
            channels=1,
            dtype="float32",
            samplerate=self.sample_rate,
        )

        stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            latency="low",
            device=self.device,
            callback=self._callback,
        )

        try:
            stream.start()
        except Exception:
            stream.close()
            raise

        self._stream = stream

    def stop(self) -> None:
        stream = self._stream
        self._stream = None
        if stream is None:
            return

        try:
            if stream.active:
                stream.stop()
        finally:
            stream.close()

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

    def __enter__(self) -> AudioInput:
        self.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback
        self.stop()
