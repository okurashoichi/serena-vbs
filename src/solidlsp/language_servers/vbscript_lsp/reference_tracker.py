"""ReferenceTracker for VBScript Symbol References.

This module provides functionality to track and search symbol references
in VBScript code, supporting the LSP textDocument/references functionality.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from solidlsp.language_servers.vbscript_lsp.reference import Reference

if TYPE_CHECKING:
    from solidlsp.language_servers.vbscript_lsp.parser import ParsedSymbol


# VBScript identifier pattern (case-insensitive)
# Matches valid VBScript identifiers: start with letter or underscore, followed by letters, digits, or underscores
IDENTIFIER_PATTERN = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b")


class ReferenceTracker:
    """Tracks and searches symbol references in VBScript code.

    This class maintains two indexes:
    1. By URI - for retrieving all references in a document
    2. By name (lowercase) - for fast case-insensitive reference lookup

    The tracker extracts identifier references from VBScript code,
    excluding comments and string literals.
    """

    def __init__(self) -> None:
        """Initialize an empty reference tracker."""
        # Map from URI to list of references in that document
        self._references_by_uri: dict[str, list[Reference]] = {}

        # Map from lowercase name to list of references with that name
        self._references_by_name: dict[str, list[Reference]] = {}

        # Map from URI to set of symbol names (lowercase) defined in that document
        self._definitions_by_uri: dict[str, set[str]] = {}

    def update(self, uri: str, content: str, symbols: list[ParsedSymbol]) -> None:
        """Update the reference index with references from a document.

        This replaces any existing references for the given URI.
        It extracts identifier references while excluding comments and string literals.

        Args:
            uri: Document URI
            content: Document content (source code)
            symbols: List of parsed symbols from the document (definitions)
        """
        # Remove existing references for this URI first
        self.remove(uri)

        # Build a set of defined symbol names in this document
        defined_names: set[str] = set()
        self._collect_symbol_names(symbols, defined_names)
        self._definitions_by_uri[uri] = defined_names

        # Extract references from content
        references = self._extract_references(uri, content, symbols)

        # Store in URI index
        self._references_by_uri[uri] = references

        # Store in name index
        for ref in references:
            name_lower = ref.name.lower()
            if name_lower not in self._references_by_name:
                self._references_by_name[name_lower] = []
            self._references_by_name[name_lower].append(ref)

    def remove(self, uri: str) -> None:
        """Remove all references for a document from the index.

        Args:
            uri: Document URI to remove
        """
        if uri not in self._references_by_uri:
            return

        # Remove from name index
        references_to_remove = self._references_by_uri[uri]
        for ref in references_to_remove:
            name_lower = ref.name.lower()
            if name_lower in self._references_by_name:
                self._references_by_name[name_lower] = [
                    r for r in self._references_by_name[name_lower] if r.uri != uri
                ]
                # Clean up empty lists
                if not self._references_by_name[name_lower]:
                    del self._references_by_name[name_lower]

        # Remove from URI index
        del self._references_by_uri[uri]

        # Remove definitions
        if uri in self._definitions_by_uri:
            del self._definitions_by_uri[uri]

    def find_references(
        self,
        name: str,
        include_declaration: bool = False,
    ) -> list[Reference]:
        """Find all references to a symbol by name.

        The search is case-insensitive to match VBScript's behavior.

        Args:
            name: Symbol name to find
            include_declaration: Whether to include the symbol definition itself

        Returns:
            List of Reference objects for each reference found
        """
        name_lower = name.lower()
        references = self._references_by_name.get(name_lower, [])

        if include_declaration:
            return list(references)
        else:
            # Filter out definitions
            return [r for r in references if not r.is_definition]

    def _collect_symbol_names(self, symbols: list[ParsedSymbol], names: set[str]) -> None:
        """Recursively collect all symbol names from a list of symbols.

        Args:
            symbols: List of parsed symbols
            names: Set to add names to (modified in place)
        """
        for symbol in symbols:
            names.add(symbol.name.lower())
            if symbol.children:
                self._collect_symbol_names(symbol.children, names)

    def _extract_references(
        self,
        uri: str,
        content: str,
        symbols: list[ParsedSymbol],
    ) -> list[Reference]:
        """Extract identifier references from VBScript content.

        This method scans the content for identifiers while excluding
        those that appear in comments or string literals.

        Args:
            uri: Document URI
            content: Document content
            symbols: Parsed symbols (for marking definitions)

        Returns:
            List of Reference objects
        """
        references: list[Reference] = []

        # Build a map of symbol definitions for quick lookup
        symbol_positions = self._build_symbol_position_map(symbols)

        # Process content line by line
        lines = content.split("\n")

        for line_num, line in enumerate(lines):
            # Extract references from this line, excluding comments and strings
            line_refs = self._extract_line_references(
                uri, line, line_num, symbol_positions
            )
            references.extend(line_refs)

        return references

    def _build_symbol_position_map(
        self,
        symbols: list[ParsedSymbol],
    ) -> dict[tuple[int, str], ParsedSymbol]:
        """Build a map of (line, lowercase_name) -> symbol for definition lookup.

        Args:
            symbols: Parsed symbols

        Returns:
            Dictionary mapping (line, name) to symbol
        """
        result: dict[tuple[int, str], ParsedSymbol] = {}
        self._add_symbols_to_map(symbols, result)
        return result

    def _add_symbols_to_map(
        self,
        symbols: list[ParsedSymbol],
        result: dict[tuple[int, str], ParsedSymbol],
    ) -> None:
        """Recursively add symbols to the position map.

        Args:
            symbols: Symbols to add
            result: Map to add to (modified in place)
        """
        for symbol in symbols:
            key = (symbol.range.start.line, symbol.name.lower())
            result[key] = symbol
            if symbol.children:
                self._add_symbols_to_map(symbol.children, result)

    def _extract_line_references(
        self,
        uri: str,
        line: str,
        line_num: int,
        symbol_positions: dict[tuple[int, str], ParsedSymbol],
    ) -> list[Reference]:
        """Extract identifier references from a single line.

        Args:
            uri: Document URI
            line: Line content
            line_num: Line number (0-indexed)
            symbol_positions: Map of symbol positions for definition lookup

        Returns:
            List of Reference objects from this line
        """
        references: list[Reference] = []

        # Find comment start position (if any)
        comment_start = self._find_comment_start(line)

        # Find all string literal ranges
        string_ranges = self._find_string_ranges(line, comment_start)

        # Find all identifiers
        for match in IDENTIFIER_PATTERN.finditer(line):
            identifier = match.group(1)
            start_pos = match.start()
            end_pos = match.end()

            # Skip if in comment
            if comment_start is not None and start_pos >= comment_start:
                continue

            # Skip if in string literal
            if self._is_in_range(start_pos, string_ranges):
                continue

            # Skip VBScript keywords
            if self._is_keyword(identifier):
                continue

            # Check if this is a definition
            key = (line_num, identifier.lower())
            is_definition = key in symbol_positions

            # Find container (the symbol that contains this reference)
            container_name = self._find_container(line_num, symbol_positions)

            ref = Reference(
                name=identifier,
                uri=uri,
                line=line_num,
                character=start_pos,
                end_line=line_num,
                end_character=end_pos,
                is_definition=is_definition,
                container_name=container_name,
            )
            references.append(ref)

        return references

    def _find_comment_start(self, line: str) -> int | None:
        """Find the position where a comment starts in a line.

        VBScript comments start with ' (single quote) or REM keyword.
        This method must handle ' inside string literals.

        Args:
            line: Line content

        Returns:
            Position of comment start, or None if no comment
        """
        in_string = False
        for i, char in enumerate(line):
            if char == '"':
                in_string = not in_string
            elif char == "'" and not in_string:
                return i
            elif not in_string and i + 3 <= len(line):
                # Check for REM keyword (case-insensitive)
                word_start = i == 0 or not line[i - 1].isalnum()
                if word_start and line[i : i + 3].upper() == "REM":
                    word_end = i + 3 >= len(line) or not line[i + 3].isalnum()
                    if word_end:
                        return i

        return None

    def _find_string_ranges(
        self,
        line: str,
        comment_start: int | None,
    ) -> list[tuple[int, int]]:
        """Find all string literal ranges in a line.

        VBScript strings are delimited by double quotes ("").
        Escaped quotes are represented as "".

        Args:
            line: Line content
            comment_start: Position of comment start (to limit search)

        Returns:
            List of (start, end) tuples for string ranges
        """
        ranges: list[tuple[int, int]] = []
        effective_line = line[:comment_start] if comment_start is not None else line

        in_string = False
        string_start = 0

        i = 0
        while i < len(effective_line):
            char = effective_line[i]
            if char == '"':
                if in_string:
                    # Check for escaped quote ("")
                    if i + 1 < len(effective_line) and effective_line[i + 1] == '"':
                        i += 2
                        continue
                    # End of string
                    ranges.append((string_start, i + 1))
                    in_string = False
                else:
                    # Start of string
                    string_start = i
                    in_string = True
            i += 1

        return ranges

    def _is_in_range(self, pos: int, ranges: list[tuple[int, int]]) -> bool:
        """Check if a position is within any of the given ranges.

        Args:
            pos: Position to check
            ranges: List of (start, end) ranges

        Returns:
            True if pos is within any range
        """
        for start, end in ranges:
            if start <= pos < end:
                return True
        return False

    def _is_keyword(self, identifier: str) -> bool:
        """Check if an identifier is a VBScript keyword.

        Args:
            identifier: Identifier to check

        Returns:
            True if the identifier is a keyword
        """
        keywords = {
            # Statement keywords
            "and", "as", "byref", "byval", "call", "case", "class", "const",
            "dim", "do", "each", "else", "elseif", "empty", "end", "eqv",
            "erase", "error", "execute", "exit", "explicit", "false", "for",
            "function", "get", "goto", "if", "imp", "in", "is", "let", "loop",
            "mod", "new", "next", "not", "nothing", "null", "on", "option",
            "or", "preserve", "private", "property", "public", "redim", "rem",
            "resume", "select", "set", "step", "sub", "then", "to", "true",
            "until", "wend", "while", "with", "xor",
            # Built-in functions (common ones)
            "abs", "array", "asc", "cbool", "cbyte", "ccur", "cdate", "cdbl",
            "chr", "cint", "clng", "createobject", "csng", "cstr", "date",
            "dateadd", "datediff", "datepart", "dateserial", "datevalue",
            "day", "escape", "eval", "exp", "filter", "fix", "formatcurrency",
            "formatdatetime", "formatnumber", "formatpercent", "getlocale",
            "getobject", "getref", "hex", "hour", "inputbox", "instr",
            "instrrev", "int", "isarray", "isdate", "isempty", "isnull",
            "isnumeric", "isobject", "join", "lbound", "lcase", "left", "len",
            "loadpicture", "log", "ltrim", "mid", "minute", "month",
            "monthname", "msgbox", "now", "oct", "replace", "rgb", "right",
            "rnd", "round", "rtrim", "scriptengine", "scriptenginebuildversion",
            "scriptenginemajorversion", "scriptengineminorversion", "second",
            "setlocale", "sgn", "sin", "space", "split", "sqr", "strcomp",
            "string", "strreverse", "tan", "time", "timer", "timeserial",
            "timevalue", "trim", "typename", "ubound", "ucase", "unescape",
            "vartype", "weekday", "weekdayname", "year",
        }
        return identifier.lower() in keywords

    def _find_container(
        self,
        line_num: int,
        symbol_positions: dict[tuple[int, str], ParsedSymbol],
    ) -> str | None:
        """Find the name of the symbol that contains a given line.

        This is a simplified implementation that doesn't track full nesting.

        Args:
            line_num: Line number to check
            symbol_positions: Map of symbol positions

        Returns:
            Container symbol name, or None if not in a container
        """
        # This would require more sophisticated tracking
        # For now, return None (container info would be populated when SymbolIndex integration happens)
        return None
