from __future__ import annotations

from git.remote import RemoteProgress
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn


class GitProgress(RemoteProgress):
    """Report Git clone/fetch progress to a Rich progress bar.

    This class implements GitPython's ``RemoteProgress`` interface to display
    real-time progress of Git operations (clone, fetch) using Rich's live
    progress display.
    """

    def __init__(self):
        super().__init__()
        self._progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        self._task_id = None
        self._progress.start()

    def update(self, op_code, cur_count, max_count=None, message=""):
        if self._task_id is None:
            stage = self._get_stage_label(op_code)
            self._task_id = self._progress.add_task(
                description=f"[cyan]{stage}...",
                total=max_count or 100,
            )

        if max_count is not None:
            self._progress.update(
                self._task_id,
                completed=cur_count,
                total=max_count,
            )
        else:
            self._progress.update(self._task_id, completed=cur_count)

        if op_code & RemoteProgress.END:
            self._progress.stop()

    @staticmethod
    def _get_stage_label(op_code):
        """Map a Git operation code to a human-readable stage label."""
        if op_code & RemoteProgress.COUNTING:
            return "Counting objects"
        if op_code & RemoteProgress.COMPRESSION:
            return "Compressing objects"
        if op_code & RemoteProgress.RECEIVING:
            return "Receiving objects"
        if op_code & RemoteProgress.RESOLVING:
            return "Resolving deltas"
        if op_code & RemoteProgress.WRITING:
            return "Writing objects"
        if op_code & RemoteProgress.CHECKING_OUT:
            return "Checking out files"
        if op_code & RemoteProgress.FINDING_SOURCES:
            return "Finding sources"
        return "Cloning"

    def close(self):
        """Safely stop the progress display (idempotent)."""
        if self._progress is not None:
            self._progress.stop()
