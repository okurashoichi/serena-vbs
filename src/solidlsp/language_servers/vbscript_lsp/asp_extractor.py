"""ASP Script Extractor for extracting VBScript blocks from ASP files.

This module provides functionality to extract VBScript code blocks from
Classic ASP files, handling both <% %> delimiters and <script runat="server"> tags.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ScriptBlock:
    """Represents a VBScript block extracted from an ASP file.

    Attributes:
        content: The VBScript code content (without delimiters)
        start_line: Starting line number (0-indexed)
        start_character: Starting character position on the line
        end_line: Ending line number (0-indexed)
        end_character: Ending character position on the line
        is_inline: True if this is an inline expression (<%= %>)
    """

    content: str
    start_line: int
    start_character: int
    end_line: int
    end_character: int
    is_inline: bool


# Pattern for <% ... %> blocks (excludes <%= %>)
# Uses negative lookahead to exclude inline expressions
ASP_BLOCK_PATTERN = re.compile(
    r"<%(?!=)(.*?)%>",
    re.DOTALL,
)

# Pattern for <%= ... %> inline expressions (to identify and skip)
ASP_INLINE_PATTERN = re.compile(
    r"<%=(.*?)%>",
    re.DOTALL,
)

# Pattern for <script runat="server"> blocks
# Matches variations like:
# - <script runat="server">
# - <script language="vbscript" runat="server">
# - <SCRIPT RUNAT="SERVER">
ASP_SCRIPT_TAG_PATTERN = re.compile(
    r'<script\s+[^>]*runat\s*=\s*["\']server["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


class ASPScriptExtractor:
    """Extracts VBScript blocks from ASP file content.

    This class handles extraction of server-side VBScript code from Classic ASP
    files, supporting both <% %> delimiters and <script runat="server"> tags.
    Inline expressions (<%= %>) are identified but excluded from extraction
    since they don't contain symbol definitions.
    """

    def __init__(self) -> None:
        """Initialize the ASP script extractor."""
        pass

    def extract(self, content: str) -> list[ScriptBlock]:
        """Extract all VBScript blocks from ASP content.

        Args:
            content: The ASP file content

        Returns:
            List of ScriptBlock objects containing extracted VBScript code
        """
        blocks: list[ScriptBlock] = []

        # Extract <% %> delimited blocks
        blocks.extend(self._find_delimited_blocks(content))

        # Extract <script runat="server"> blocks
        blocks.extend(self._find_script_tags(content))

        # Sort blocks by their position in the file
        blocks.sort(key=lambda b: (b.start_line, b.start_character))

        return blocks

    def _find_delimited_blocks(self, content: str) -> list[ScriptBlock]:
        """Find all <% %> delimited blocks (excluding <%= %>).

        Args:
            content: The ASP file content

        Returns:
            List of ScriptBlock objects for <% %> blocks
        """
        blocks: list[ScriptBlock] = []

        for match in ASP_BLOCK_PATTERN.finditer(content):
            block_content = match.group(1)

            # Calculate position
            start_pos = match.start()
            end_pos = match.end()

            start_line, start_char = self._calculate_position(content, start_pos)
            end_line, end_char = self._calculate_position(content, end_pos)

            block = ScriptBlock(
                content=block_content,
                start_line=start_line,
                start_character=start_char,
                end_line=end_line,
                end_character=end_char,
                is_inline=False,
            )
            blocks.append(block)

        return blocks

    def _find_script_tags(self, content: str) -> list[ScriptBlock]:
        """Find all <script runat="server"> blocks.

        Args:
            content: The ASP file content

        Returns:
            List of ScriptBlock objects for script tag blocks
        """
        blocks: list[ScriptBlock] = []

        for match in ASP_SCRIPT_TAG_PATTERN.finditer(content):
            block_content = match.group(1)

            # Calculate position
            start_pos = match.start()
            end_pos = match.end()

            start_line, start_char = self._calculate_position(content, start_pos)
            end_line, end_char = self._calculate_position(content, end_pos)

            block = ScriptBlock(
                content=block_content,
                start_line=start_line,
                start_character=start_char,
                end_line=end_line,
                end_character=end_char,
                is_inline=False,
            )
            blocks.append(block)

        return blocks

    def _calculate_position(self, content: str, char_offset: int) -> tuple[int, int]:
        """Calculate line number and character position from character offset.

        Args:
            content: The full content string
            char_offset: Character offset from the start of content

        Returns:
            Tuple of (line_number, character_position) both 0-indexed
        """
        # Count newlines before this position to get line number
        text_before = content[:char_offset]
        line_number = text_before.count("\n")

        # Find the start of the current line
        last_newline = text_before.rfind("\n")
        if last_newline == -1:
            # First line, character position is just the offset
            char_position = char_offset
        else:
            # Character position is offset from last newline
            char_position = char_offset - last_newline - 1

        return line_number, char_position
