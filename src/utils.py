"""Utility classes for building and saving TeX files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class FileBuilder:
    """Incrementally builds a text file from lines and other FileBuilders."""

    def __init__(self, file_path: Optional[Path] = None) -> None:
        """Initialize a FileBuilder, optionally loading content from a file.

        Args:
            file_path: Path to an existing file to load. If None, starts empty.

        Raises:
            FileNotFoundError: If file_path is provided but does not exist.
        """
        if file_path is None:
            self.lines: list[str] = []
        else:
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found.")
            with file_path.open("r") as file:
                self.lines = [line.rstrip() for line in file]

    def add_line(self, line: str) -> FileBuilder:
        """Append a stripped line to the builder.

        Args:
            line: The line of text to add.

        Returns:
            Self for method chaining.
        """
        self.lines.append(line.strip())
        return self

    def add_new_line(self, n: int = 1) -> FileBuilder:
        """Append one or more blank lines.

        Args:
            n: Number of blank lines to add.

        Returns:
            Self for method chaining.
        """
        for _ in range(n):
            self.lines.append("")
        return self

    def add_file_builder(self, file_builder: FileBuilder) -> FileBuilder:
        """Append all lines from another FileBuilder.

        Args:
            file_builder: The FileBuilder whose lines will be appended.

        Returns:
            Self for method chaining.
        """
        self.lines.extend(file_builder.lines)
        return self

    def get_str(self) -> str:
        """Return all lines joined by newlines."""
        return "\n".join(self.lines)

    def save(self, file_path: Path) -> None:
        """Write the built content to a file.

        Args:
            file_path: Destination path.
        """
        with file_path.open("w") as file:
            file.write(self.get_str())
