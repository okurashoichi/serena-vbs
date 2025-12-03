"""VBScript Parser for extracting symbols from VBScript source code.

This module provides functionality to parse VBScript (.vbs) and ASP (.asp, .inc) files,
extracting Function, Sub, Class, and Property definitions as LSP-compatible symbols.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lsprotocol import types


@dataclass
class Range:
    """Represents a range in a text document."""

    start: Position
    end: Position


@dataclass
class Position:
    """Represents a position in a text document (0-indexed)."""

    line: int
    character: int


@dataclass
class ParsedSymbol:
    """Represents a parsed symbol from VBScript code.

    Attributes:
        name: The symbol name
        kind: LSP SymbolKind (12 = Function, 5 = Class, 7 = Property, etc.)
        range: The full range of the symbol in the document
        selection_range: The range of the symbol name for selection
        children: Nested symbols (e.g., methods inside a class)
    """

    name: str
    kind: int  # SymbolKind value
    range: Range
    selection_range: Range
    children: list[ParsedSymbol] = field(default_factory=list)

    def to_document_symbol(self) -> types.DocumentSymbol:
        """Convert to LSP DocumentSymbol format."""
        from lsprotocol import types

        children = [child.to_document_symbol() for child in self.children]

        return types.DocumentSymbol(
            name=self.name,
            kind=types.SymbolKind(self.kind),
            range=types.Range(
                start=types.Position(line=self.range.start.line, character=self.range.start.character),
                end=types.Position(line=self.range.end.line, character=self.range.end.character),
            ),
            selection_range=types.Range(
                start=types.Position(line=self.selection_range.start.line, character=self.selection_range.start.character),
                end=types.Position(line=self.selection_range.end.line, character=self.selection_range.end.character),
            ),
            children=children if children else None,
        )


# SymbolKind constants (from LSP spec)
SYMBOL_KIND_CLASS = 5
SYMBOL_KIND_PROPERTY = 7
SYMBOL_KIND_FUNCTION = 12
SYMBOL_KIND_VARIABLE = 13
SYMBOL_KIND_CONSTANT = 14


# VBScript syntax patterns (case-insensitive)
# Note: Use [ \t]* instead of \s* to avoid matching newlines in leading whitespace
FUNCTION_PATTERN = re.compile(
    r"^[ \t]*(public[ \t]+|private[ \t]+)?[ \t]*function[ \t]+(\w+)[ \t]*\(([^)]*)\)",
    re.IGNORECASE | re.MULTILINE,
)

SUB_PATTERN = re.compile(
    r"^[ \t]*(public[ \t]+|private[ \t]+)?[ \t]*sub[ \t]+(\w+)[ \t]*\(([^)]*)\)",
    re.IGNORECASE | re.MULTILINE,
)

END_FUNCTION_PATTERN = re.compile(
    r"^\s*end\s+function",
    re.IGNORECASE | re.MULTILINE,
)

END_SUB_PATTERN = re.compile(
    r"^\s*end\s+sub",
    re.IGNORECASE | re.MULTILINE,
)

# Class patterns
CLASS_PATTERN = re.compile(
    r"^[ \t]*class[ \t]+(\w+)",
    re.IGNORECASE | re.MULTILINE,
)

END_CLASS_PATTERN = re.compile(
    r"^[ \t]*end[ \t]+class",
    re.IGNORECASE | re.MULTILINE,
)

# Property patterns (Get, Let, Set)
PROPERTY_PATTERN = re.compile(
    r"^[ \t]*(public[ \t]+|private[ \t]+)?[ \t]*property[ \t]+(get|let|set)[ \t]+(\w+)[ \t]*\(([^)]*)\)",
    re.IGNORECASE | re.MULTILINE,
)

END_PROPERTY_PATTERN = re.compile(
    r"^[ \t]*end[ \t]+property",
    re.IGNORECASE | re.MULTILINE,
)


class VBScriptParser:
    """Parser for extracting symbols from VBScript source code."""

    def __init__(self) -> None:
        """Initialize the VBScript parser."""
        pass

    def parse(self, content: str, uri: str = "", line_offset: int = 0) -> list[ParsedSymbol]:
        """Parse source code and extract symbols.

        Args:
            content: VBScript or ASP source code
            uri: Document URI (used to determine file type)
            line_offset: Line number offset for ASP blocks

        Returns:
            List of parsed symbols
        """
        # Determine if this is an ASP file
        if uri.lower().endswith(".asp"):
            return self.parse_asp(content)
        else:
            return self.parse_vbscript(content, line_offset)

    def parse_vbscript(self, content: str, line_offset: int = 0) -> list[ParsedSymbol]:
        """Parse pure VBScript code and extract symbols.

        Args:
            content: VBScript source code
            line_offset: Line number offset (for ASP blocks)

        Returns:
            List of parsed symbols
        """
        # Extract classes with their members
        class_symbols = self._extract_classes(content, line_offset)

        # Get the ranges covered by classes to exclude from top-level extraction
        class_ranges = [(cls.range.start.line, cls.range.end.line) for cls in class_symbols]

        # Extract top-level functions (not inside classes)
        all_functions = self._extract_functions(content, line_offset)
        top_level_functions = self._filter_top_level(all_functions, class_ranges)

        # Extract top-level subs (not inside classes)
        all_subs = self._extract_subs(content, line_offset)
        top_level_subs = self._filter_top_level(all_subs, class_ranges)

        # Extract top-level properties (not inside classes)
        all_properties = self._extract_properties(content, line_offset)
        top_level_properties = self._filter_top_level(all_properties, class_ranges)

        # Combine all symbols
        symbols: list[ParsedSymbol] = []
        symbols.extend(class_symbols)
        symbols.extend(top_level_functions)
        symbols.extend(top_level_subs)
        symbols.extend(top_level_properties)

        # Sort symbols by their start position
        symbols.sort(key=lambda s: (s.range.start.line, s.range.start.character))

        return symbols

    def _filter_top_level(
        self, symbols: list[ParsedSymbol], class_ranges: list[tuple[int, int]]
    ) -> list[ParsedSymbol]:
        """Filter symbols to only include those not inside class ranges."""
        result = []
        for symbol in symbols:
            is_inside_class = any(
                start <= symbol.range.start.line <= end for start, end in class_ranges
            )
            if not is_inside_class:
                result.append(symbol)
        return result

    def parse_asp(self, content: str) -> list[ParsedSymbol]:
        """Parse ASP file and extract VBScript symbols.

        This method extracts VBScript blocks from ASP files using ASPScriptExtractor,
        then parses each block with the appropriate line offset to convert positions
        to original ASP file coordinates.

        Args:
            content: ASP file content

        Returns:
            List of parsed symbols from all VBScript blocks
        """
        from solidlsp.language_servers.vbscript_lsp.asp_extractor import ASPScriptExtractor

        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        all_symbols: list[ParsedSymbol] = []

        for block in blocks:
            # Skip inline expressions (they don't contain symbol definitions)
            if block.is_inline:
                continue

            # Parse the block content with the line offset from the original ASP file
            # The block.content already contains the VBScript code extracted from the ASP file.
            # The block.start_line is where the <% or <script> tag starts.
            #
            # The position calculation works as follows:
            # - block.content may start with a newline (e.g., "<%\nFunction..." -> content is "\nFunction...")
            # - parse_vbscript counts newlines in block.content to determine line numbers
            # - We use block.start_line as the offset, which correctly positions symbols
            #   because the first newline in block.content moves us to the next line
            #
            # Example: <%\nFunction... (block.start_line=2)
            # - block.content = "\nFunction..."
            # - parse_vbscript finds Function at line 1 within block.content
            # - With offset 2, final line = 1 + 2 = 3 (correct!)
            line_offset = block.start_line

            # Parse the VBScript content
            symbols = self.parse_vbscript(block.content, line_offset)
            all_symbols.extend(symbols)

        # Sort all symbols by their position in the file
        all_symbols.sort(key=lambda s: (s.range.start.line, s.range.start.character))

        return all_symbols

    def _extract_functions(self, content: str, line_offset: int) -> list[ParsedSymbol]:
        """Extract Function definitions from VBScript code."""
        return self._extract_callable(
            content, line_offset, FUNCTION_PATTERN, END_FUNCTION_PATTERN, "function"
        )

    def _extract_subs(self, content: str, line_offset: int) -> list[ParsedSymbol]:
        """Extract Sub definitions from VBScript code."""
        return self._extract_callable(content, line_offset, SUB_PATTERN, END_SUB_PATTERN, "sub")

    def _extract_classes(self, content: str, line_offset: int) -> list[ParsedSymbol]:
        """Extract Class definitions from VBScript code with their members."""
        symbols: list[ParsedSymbol] = []
        lines = content.split("\n")

        for match in CLASS_PATTERN.finditer(content):
            class_name = match.group(1)

            # Calculate line number from character position
            start_char = match.start()
            start_line = content[:start_char].count("\n") + line_offset

            # Find the name position within the match
            match_text = match.group(0)
            name_start_in_match = match_text.lower().find("class") + len("class")
            while name_start_in_match < len(match_text) and match_text[name_start_in_match].isspace():
                name_start_in_match += 1

            # Calculate name column position
            line_start = content.rfind("\n", 0, start_char) + 1
            name_col = (start_char - line_start) + name_start_in_match

            # Find corresponding End Class
            end_match = END_CLASS_PATTERN.search(content, match.end())
            if end_match:
                end_line = content[:end_match.start()].count("\n") + line_offset
            else:
                end_line = start_line

            # Calculate end column
            if end_line - line_offset < len(lines):
                end_col = len(lines[end_line - line_offset])
            else:
                end_col = 0

            # Extract the class body content
            class_body_start = match.end()
            class_body_end = end_match.start() if end_match else len(content)
            class_body = content[class_body_start:class_body_end]

            # Parse members within the class body
            class_body_line_offset = content[:class_body_start].count("\n") + line_offset
            children: list[ParsedSymbol] = []

            # Extract functions within class
            children.extend(self._extract_callable(
                class_body, class_body_line_offset, FUNCTION_PATTERN, END_FUNCTION_PATTERN, "function"
            ))

            # Extract subs within class
            children.extend(self._extract_callable(
                class_body, class_body_line_offset, SUB_PATTERN, END_SUB_PATTERN, "sub"
            ))

            # Extract properties within class
            children.extend(self._extract_properties(class_body, class_body_line_offset))

            # Sort children by position
            children.sort(key=lambda s: (s.range.start.line, s.range.start.character))

            symbol = ParsedSymbol(
                name=class_name,
                kind=SYMBOL_KIND_CLASS,
                range=Range(
                    start=Position(line=start_line, character=start_char - line_start),
                    end=Position(line=end_line, character=end_col),
                ),
                selection_range=Range(
                    start=Position(line=start_line, character=name_col),
                    end=Position(line=start_line, character=name_col + len(class_name)),
                ),
                children=children,
            )
            symbols.append(symbol)

        return symbols

    def _extract_properties(self, content: str, line_offset: int) -> list[ParsedSymbol]:
        """Extract Property definitions from VBScript code."""
        symbols: list[ParsedSymbol] = []
        lines = content.split("\n")

        for match in PROPERTY_PATTERN.finditer(content):
            prop_name = match.group(3)  # Group 3 is the property name

            # Calculate line number from character position
            start_char = match.start()
            start_line = content[:start_char].count("\n") + line_offset

            # Find the name position within the match
            match_text = match.group(0)
            # Find "property" then skip "get/let/set" to find the name
            prop_keyword_pos = match_text.lower().find("property")
            name_start_in_match = prop_keyword_pos + len("property")
            # Skip whitespace
            while name_start_in_match < len(match_text) and match_text[name_start_in_match].isspace():
                name_start_in_match += 1
            # Skip get/let/set keyword
            prop_type = match.group(2).lower()
            name_start_in_match += len(prop_type)
            # Skip whitespace after get/let/set
            while name_start_in_match < len(match_text) and match_text[name_start_in_match].isspace():
                name_start_in_match += 1

            # Calculate name column position
            line_start = content.rfind("\n", 0, start_char) + 1
            name_col = (start_char - line_start) + name_start_in_match

            # Find corresponding End Property
            end_line = self._find_end_pattern(content, match.end(), END_PROPERTY_PATTERN, line_offset)
            if end_line == -1:
                end_line = start_line

            # Calculate end column
            if end_line - line_offset < len(lines):
                end_col = len(lines[end_line - line_offset])
            else:
                end_col = 0

            symbol = ParsedSymbol(
                name=prop_name,
                kind=SYMBOL_KIND_PROPERTY,
                range=Range(
                    start=Position(line=start_line, character=start_char - line_start),
                    end=Position(line=end_line, character=end_col),
                ),
                selection_range=Range(
                    start=Position(line=start_line, character=name_col),
                    end=Position(line=start_line, character=name_col + len(prop_name)),
                ),
            )
            symbols.append(symbol)

        return symbols

    def _extract_callable(
        self,
        content: str,
        line_offset: int,
        start_pattern: re.Pattern[str],
        end_pattern: re.Pattern[str],
        keyword: str,
    ) -> list[ParsedSymbol]:
        """Extract callable definitions (Function or Sub) from VBScript code.

        Args:
            content: VBScript source code
            line_offset: Line number offset
            start_pattern: Regex pattern for the start of the callable
            end_pattern: Regex pattern for the end of the callable
            keyword: The keyword to search for in the match ('function' or 'sub')

        Returns:
            List of callable symbols
        """
        symbols: list[ParsedSymbol] = []
        lines = content.split("\n")

        for match in start_pattern.finditer(content):
            name = match.group(2)

            # Calculate line number from character position
            start_char = match.start()
            start_line = content[:start_char].count("\n") + line_offset

            # Find the name position within the match
            match_text = match.group(0)
            name_start_in_match = match_text.lower().find(keyword) + len(keyword)
            # Skip whitespace after keyword
            while name_start_in_match < len(match_text) and match_text[name_start_in_match].isspace():
                name_start_in_match += 1

            # Calculate name column position
            line_start = content.rfind("\n", 0, start_char) + 1
            name_col = (start_char - line_start) + name_start_in_match

            # Find corresponding End statement
            end_line = self._find_end_pattern(content, match.end(), end_pattern, line_offset)
            if end_line == -1:
                end_line = start_line

            # Calculate end column
            if end_line - line_offset < len(lines):
                end_col = len(lines[end_line - line_offset])
            else:
                end_col = 0

            symbol = ParsedSymbol(
                name=name,
                kind=SYMBOL_KIND_FUNCTION,
                range=Range(
                    start=Position(line=start_line, character=start_char - line_start),
                    end=Position(line=end_line, character=end_col),
                ),
                selection_range=Range(
                    start=Position(line=start_line, character=name_col),
                    end=Position(line=start_line, character=name_col + len(name)),
                ),
            )
            symbols.append(symbol)

        return symbols

    def _find_end_pattern(self, content: str, start_pos: int, end_pattern: re.Pattern[str], line_offset: int) -> int:
        """Find the line number of an End pattern after a given position.

        Args:
            content: Source code
            start_pos: Position to start searching from
            end_pattern: Regex pattern for the end statement
            line_offset: Line number offset

        Returns:
            Line number of the end statement, or -1 if not found
        """
        match = end_pattern.search(content, start_pos)
        if match:
            return content[:match.start()].count("\n") + line_offset
        return -1
