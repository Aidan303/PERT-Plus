"""
Async job runner using QThread.
Supports progress reporting, best-effort cancel, and force-stop.
"""
from __future__ import annotations

import traceback
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QThread, Signal


class JobWorker(QThread):
    """
    Runs a single callable in a background thread.

    Signals:
        progress_updated(current, total, message)
        log_updated(message)
        finished(result)           -- result is the return value of the callable
        error_occurred(message)    -- emitted on exception
    """

    progress_updated = Signal(int, int, str)
    log_updated = Signal(str)
    finished = Signal(object)
    error_occurred = Signal(str)

    def __init__(
        self,
        action_fn: Callable[..., Any],
        action_kwargs: Dict[str, Any],
        parent=None,
    ):
        super().__init__(parent)
        self._action_fn = action_fn
        self._action_kwargs = action_kwargs
        self._cancelled = False
        self._force_stop = False

    # ── Cancellation ──────────────────────────────────────────────────────────

    def request_cancel(self) -> None:
        """Best-effort cancel: checked between steps inside the engine."""
        self._cancelled = True

    def request_force_stop(self) -> None:
        """Terminate the thread immediately (last resort)."""
        self._force_stop = True
        self._cancelled = True
        self.terminate()

    def is_cancelled(self) -> bool:
        return self._cancelled

    # ── Progress callbacks (injected into engine functions) ───────────────────

    def _progress_cb(self, current: int, total: int, message: str) -> None:
        self.progress_updated.emit(current, total, message)
        self.log_updated.emit(message)

    def _cancel_check(self) -> bool:
        return self._cancelled

    # ── Thread entry point ────────────────────────────────────────────────────

    def run(self) -> None:
        kwargs = dict(self._action_kwargs)
        # Inject callbacks if the function accepts them
        import inspect
        sig = inspect.signature(self._action_fn)
        if "progress_cb" in sig.parameters:
            kwargs["progress_cb"] = self._progress_cb
        if "cancel_check" in sig.parameters:
            kwargs["cancel_check"] = self._cancel_check

        try:
            result = self._action_fn(**kwargs)
            if not self._force_stop:
                self.finished.emit(result)
        except InterruptedError as exc:
            self.log_updated.emit(f"[Cancelled] {exc}")
            self.error_occurred.emit(f"Cancelled: {exc}")
        except Exception as exc:
            tb = traceback.format_exc()
            self.log_updated.emit(f"[ERROR] {exc}\n{tb}")
            self.error_occurred.emit(str(exc))


class JobManager:
    """
    Manages a queue of JobWorker instances.
    Only one job runs at a time; the next is started when the current finishes.
    """

    def __init__(self):
        self._queue: list[JobWorker] = []
        self._current: Optional[JobWorker] = None

    @property
    def is_running(self) -> bool:
        return self._current is not None and self._current.isRunning()

    def submit(self, worker: JobWorker) -> None:
        self._queue.append(worker)
        if not self.is_running:
            self._start_next()

    def _start_next(self) -> None:
        if not self._queue:
            self._current = None
            return
        worker = self._queue.pop(0)
        self._current = worker
        worker.finished.connect(self._on_job_done)
        worker.error_occurred.connect(self._on_job_done)
        worker.start()

    def _on_job_done(self, *_) -> None:
        self._start_next()

    def cancel_current(self) -> None:
        if self._current and self._current.isRunning():
            self._current.request_cancel()

    def force_stop_current(self) -> None:
        if self._current and self._current.isRunning():
            self._current.request_force_stop()
            self._current = None
            self._start_next()

    def clear_queue(self) -> None:
        self._queue.clear()
