"""Include Directive Parser for ASP files.

This module provides the IncludeDirectiveParser class for extracting and parsing
ASP include directives (<!--#include file="..." --> and <!--#include virtual="..." -->)
from ASP/VBScript source files.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from solidlsp.language_servers.vbscript_lsp.include_directive import IncludeDirective

# Regular expression pattern for ASP include directives
# Matches: <!--#include file="path"--> or <!--#include virtual="path"-->
# Case-insensitive, allows extra whitespace
INCLUDE_PATTERN = re.compile(
    r'<!--\s*#include\s+(file|virtual)\s*=\s*"([^"]*)"\s*-->',
    re.IGNORECASE,
)


class IncludeDirectiveParser:
    """Parser for extracting ASP include directives from source files.

    This class extracts include directives from ASP file content and resolves
    their paths to file URIs. It supports both file (relative) and virtual
    (workspace-relative) include types.
    """

    def __init__(self, workspace_root: str | None = None) -> None:
        """Initialize the parser.

        Args:
            workspace_root: The workspace root directory for resolving virtual paths.
                           Can be a file path (not URI).
        """
        self._workspace_root = workspace_root

    def extract_includes(
        self,
        content: str,
        source_uri: str,
    ) -> list[IncludeDirective]:
        """Extract include directives from ASP content.

        Args:
            content: The ASP file content to parse.
            source_uri: The file URI of the source file being parsed.

        Returns:
            A list of IncludeDirective objects for each detected include.
        """
        directives: list[IncludeDirective] = []

        # Build a line index for position calculation
        line_starts = self._build_line_index(content)

        for match in INCLUDE_PATTERN.finditer(content):
            include_type = match.group(1).lower()
            raw_path = match.group(2)

            # Calculate position
            start_pos = match.start()
            end_pos = match.end()
            line, character = self._offset_to_position(start_pos, line_starts)
            end_line, end_character = self._offset_to_position(end_pos, line_starts)

            # Resolve path
            resolved_uri, is_valid, error_message = self._resolve_path(
                include_type, raw_path, source_uri
            )

            directive = IncludeDirective(
                include_type=include_type,  # type: ignore[arg-type]
                raw_path=raw_path,
                resolved_uri=resolved_uri,
                line=line,
                character=character,
                end_line=end_line,
                end_character=end_character,
                is_valid=is_valid,
                error_message=error_message,
            )
            directives.append(directive)

        return directives

    def _build_line_index(self, content: str) -> list[int]:
        """Build an index of line start positions.

        Args:
            content: The source content.

        Returns:
            A list where index i contains the character offset of line i.
        """
        line_starts = [0]
        for i, char in enumerate(content):
            if char == "\n":
                line_starts.append(i + 1)
        return line_starts

    def _offset_to_position(
        self, offset: int, line_starts: list[int]
    ) -> tuple[int, int]:
        """Convert a character offset to line and column.

        Args:
            offset: The character offset in the content.
            line_starts: The line start index from _build_line_index.

        Returns:
            A tuple of (line, character) where both are 0-indexed.
        """
        # Binary search for the line
        low, high = 0, len(line_starts) - 1
        while low < high:
            mid = (low + high + 1) // 2
            if line_starts[mid] <= offset:
                low = mid
            else:
                high = mid - 1

        line = low
        character = offset - line_starts[line]
        return line, character

    def _resolve_path(
        self,
        include_type: str,
        raw_path: str,
        source_uri: str,
    ) -> tuple[str | None, bool, str | None]:
        """Resolve an include path to an absolute file URI.

        Args:
            include_type: Either "file" or "virtual".
            raw_path: The raw path from the include directive.
            source_uri: The file URI of the source file.

        Returns:
            A tuple of (resolved_uri, is_valid, error_message).
        """
        # Check for empty path
        if not raw_path:
            return None, False, "Empty path in include directive"

        if include_type == "file":
            return self._resolve_file_path(raw_path, source_uri)
        else:  # virtual
            return self._resolve_virtual_path(raw_path)

    def _resolve_file_path(
        self, raw_path: str, source_uri: str
    ) -> tuple[str | None, bool, str | None]:
        """Resolve a file-type include path relative to the source file.

        Args:
            raw_path: The relative path from the include directive.
            source_uri: The file URI of the source file.

        Returns:
            A tuple of (resolved_uri, is_valid, error_message).
        """
        # Parse the source URI to get the directory
        parsed = urlparse(source_uri)
        source_path = Path(unquote(parsed.path))
        source_dir = source_path.parent

        # Normalize backslashes to forward slashes for cross-platform compatibility
        normalized_path = raw_path.replace("\\", "/")

        # Resolve the path relative to source directory
        resolved_path = (source_dir / normalized_path).resolve()

        # Convert back to file URI
        resolved_uri = f"file://{resolved_path}"

        return resolved_uri, True, None

    def _resolve_virtual_path(
        self, raw_path: str
    ) -> tuple[str | None, bool, str | None]:
        """Resolve a virtual-type include path relative to workspace root.

        Args:
            raw_path: The virtual path (starting with /) from the include directive.

        Returns:
            A tuple of (resolved_uri, is_valid, error_message).
        """
        if self._workspace_root is None:
            return (
                None,
                False,
                "Cannot resolve virtual path: workspace root not configured",
            )

        # Virtual paths start with / but are relative to workspace root
        # Strip the leading / if present
        relative_path = raw_path.lstrip("/")

        # Normalize backslashes
        normalized_path = relative_path.replace("\\", "/")

        # Resolve against workspace root
        workspace_path = Path(self._workspace_root)
        resolved_path = (workspace_path / normalized_path).resolve()

        # Convert to file URI
        resolved_uri = f"file://{resolved_path}"

        return resolved_uri, True, None
