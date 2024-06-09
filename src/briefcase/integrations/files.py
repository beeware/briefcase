from __future__ import annotations

from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_fixed

from briefcase.integrations.base import Tool, ToolCache


class Files(Tool):
    name = "files"
    full_name = "Files"

    @classmethod
    def verify_install(cls, tools: ToolCache, **kwargs) -> Files:
        """Make files available in tool cache."""
        # short circuit since already verified and available
        if hasattr(tools, "files"):
            return tools.files

        tools.files = Files(tools=tools)
        return tools.files

    @retry(wait=wait_fixed(0.2), stop=stop_after_attempt(25))
    def path_rename(self, old_path: Path, new_path: object):
        """Using tenacity for a retry policy on pathlib rename.

        Windows does not like renaming a dir in a path with an opened file.
        """
        old_path.rename(new_path)
