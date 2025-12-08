"""Symbol Index for VBScript Language Server.

This module provides functionality to index and search symbols across
documents in a workspace, supporting Go to Definition and Find References.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from solidlsp.language_servers.vbscript_lsp.reference_tracker import ReferenceTracker

if TYPE_CHECKING:
    from lsprotocol import types

    from solidlsp.language_servers.vbscript_lsp.parser import ParsedSymbol


@dataclass
class IndexedSymbol:
    """Represents an indexed symbol for fast lookup.

    Attributes:
        name: The symbol name
        kind: LSP SymbolKind value (5=Class, 7=Property, 12=Function, etc.)
        uri: Document URI where the symbol is defined
        start_line: Starting line number (0-indexed)
        start_character: Starting character position
        end_line: Ending line number (0-indexed)
        end_character: Ending character position
        container_name: Name of the containing symbol (e.g., class name)
    """

    name: str
    kind: int
    uri: str
    start_line: int
    start_character: int
    end_line: int
    end_character: int
    container_name: str | None = None


class SymbolIndex:
    """Index for tracking symbols across documents in a workspace.

    This class maintains two indexes:
    1. By URI - for retrieving all symbols in a document
    2. By name (lowercase) - for fast case-insensitive symbol lookup

    The index supports Go to Definition (find_definition) and
    Find References (find_references) operations.
    """

    def __init__(self) -> None:
        """Initialize an empty symbol index."""
        # Map from URI to list of symbols in that document
        self._symbols_by_uri: dict[str, list[IndexedSymbol]] = {}

        # Map from lowercase name to list of symbols with that name
        self._symbols_by_name: dict[str, list[IndexedSymbol]] = {}

        # Reference tracker for finding symbol references
        self._reference_tracker: ReferenceTracker = ReferenceTracker()

        # Map from URI to document content (for cross-file reference search)
        self._documents_content: dict[str, str] = {}

    def update(self, uri: str, content: str, symbols: list[ParsedSymbol]) -> None:
        """Update the index with symbols from a document.

        This replaces any existing symbols for the given URI.
        Symbols are flattened (class members are indexed at the top level).

        Args:
            uri: Document URI
            content: Document content (source code)
            symbols: List of parsed symbols from the document
        """
        # Remove existing symbols for this URI first
        self.remove(uri)

        # Flatten symbols (including nested class members)
        indexed_symbols = self._flatten_symbols(uri, symbols)

        # Store in URI index
        self._symbols_by_uri[uri] = indexed_symbols

        # Store in name index
        for symbol in indexed_symbols:
            name_lower = symbol.name.lower()
            if name_lower not in self._symbols_by_name:
                self._symbols_by_name[name_lower] = []
            self._symbols_by_name[name_lower].append(symbol)

        # Update reference tracker
        self._reference_tracker.update(uri, content, symbols)

        # Store document content for cross-file reference search
        self._documents_content[uri] = content

    def remove(self, uri: str) -> None:
        """Remove all symbols for a document from the index.

        Args:
            uri: Document URI to remove
        """
        # Remove from reference tracker first
        self._reference_tracker.remove(uri)

        # Remove document content
        if uri in self._documents_content:
            del self._documents_content[uri]

        if uri not in self._symbols_by_uri:
            return

        # Remove from name index
        symbols_to_remove = self._symbols_by_uri[uri]
        for symbol in symbols_to_remove:
            name_lower = symbol.name.lower()
            if name_lower in self._symbols_by_name:
                self._symbols_by_name[name_lower] = [
                    s for s in self._symbols_by_name[name_lower] if s.uri != uri
                ]
                # Clean up empty lists
                if not self._symbols_by_name[name_lower]:
                    del self._symbols_by_name[name_lower]

        # Remove from URI index
        del self._symbols_by_uri[uri]

    def find_definition(self, name: str) -> IndexedSymbol | None:
        """Find the definition of a symbol by name.

        The search is case-insensitive to match VBScript's behavior.

        Args:
            name: Symbol name to find

        Returns:
            IndexedSymbol if found, None otherwise
        """
        name_lower = name.lower()
        symbols = self._symbols_by_name.get(name_lower)
        if symbols:
            return symbols[0]
        return None

    def find_definition_in_scope(
        self, name: str, scope_uris: list[str]
    ) -> IndexedSymbol | None:
        """Find the first definition of a symbol within the specified URIs.

        The search is case-insensitive to match VBScript's behavior.
        Only searches within the provided URI list.

        Args:
            name: Symbol name to find
            scope_uris: List of URIs to search within

        Returns:
            IndexedSymbol if found in scope, None otherwise
        """
        if not scope_uris:
            return None

        name_lower = name.lower()
        symbols = self._symbols_by_name.get(name_lower)
        if not symbols:
            return None

        # Convert to set for O(1) lookup
        scope_set = set(scope_uris)

        for symbol in symbols:
            if symbol.uri in scope_set:
                return symbol

        return None

    def find_definitions_in_scope(
        self, name: str, scope_uris: list[str]
    ) -> list[IndexedSymbol]:
        """Find all definitions of a symbol within the specified URIs.

        The search is case-insensitive to match VBScript's behavior.
        Only searches within the provided URI list.

        Args:
            name: Symbol name to find
            scope_uris: List of URIs to search within

        Returns:
            List of IndexedSymbol objects found in scope
        """
        if not scope_uris:
            return []

        name_lower = name.lower()
        symbols = self._symbols_by_name.get(name_lower)
        if not symbols:
            return []

        # Convert to set for O(1) lookup
        scope_set = set(scope_uris)

        return [symbol for symbol in symbols if symbol.uri in scope_set]

    def find_references(
        self, name: str, include_declaration: bool = False
    ) -> list[types.Location]:
        """Find all references to a symbol by name.

        The search is case-insensitive to match VBScript's behavior.
        This method now uses the ReferenceTracker to find actual references
        (calls, usages) in addition to symbol declarations.

        Args:
            name: Symbol name to find
            include_declaration: Whether to include the declaration itself

        Returns:
            List of Location objects for each reference
        """
        from lsprotocol import types

        # Get references from the reference tracker
        refs = self._reference_tracker.find_references(name, include_declaration)

        # Convert References to Location objects
        locations: list[types.Location] = []
        for ref in refs:
            locations.append(ref.to_location())

        return locations

    def get_symbols_in_document(self, uri: str) -> list[IndexedSymbol]:
        """Get all indexed symbols in a document.

        Args:
            uri: Document URI

        Returns:
            List of IndexedSymbol objects (empty list if document not found)
        """
        return self._symbols_by_uri.get(uri, [])

    def get_document_content(self, uri: str) -> str | None:
        """Get the content of an indexed document.

        Args:
            uri: Document URI

        Returns:
            Document content if indexed, None otherwise
        """
        return self._documents_content.get(uri)

    def _flatten_symbols(
        self,
        uri: str,
        symbols: list[ParsedSymbol],
        container_name: str | None = None,
    ) -> list[IndexedSymbol]:
        """Flatten a symbol tree into a list of IndexedSymbol objects.

        This recursively processes nested symbols (e.g., class members)
        and includes them in the flat list with their container_name set.

        Args:
            uri: Document URI
            symbols: List of parsed symbols (may have children)
            container_name: Name of the containing symbol (for nested symbols)

        Returns:
            Flat list of IndexedSymbol objects
        """
        result: list[IndexedSymbol] = []

        for symbol in symbols:
            indexed = IndexedSymbol(
                name=symbol.name,
                kind=symbol.kind,
                uri=uri,
                start_line=symbol.range.start.line,
                start_character=symbol.range.start.character,
                end_line=symbol.range.end.line,
                end_character=symbol.range.end.character,
                container_name=container_name,
            )
            result.append(indexed)

            # Recursively process children (e.g., class members)
            if symbol.children:
                result.extend(
                    self._flatten_symbols(uri, symbol.children, symbol.name)
                )

        return result
