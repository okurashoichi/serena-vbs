"""VBScript Language Server using pygls.

This module implements a Language Server Protocol (LSP) server for VBScript
using the pygls framework. It provides symbol extraction, go-to-definition,
and find-references functionality.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from solidlsp.language_servers.vbscript_lsp.index import SymbolIndex
from solidlsp.language_servers.vbscript_lsp.parser import VBScriptParser

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Word pattern for VBScript identifiers
WORD_PATTERN = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


def get_word_at_position(content: str, position: types.Position) -> str | None:
    """Extract the word at the given position in the content.

    Args:
        content: The document content
        position: The cursor position (line, character)

    Returns:
        The word at the position, or None if no word is found
    """
    lines = content.split("\n")

    # Check if line is valid
    if position.line < 0 or position.line >= len(lines):
        return None

    line = lines[position.line]

    # Check if character position is valid
    if position.character < 0 or position.character > len(line):
        return None

    # Find all words in the line and check which one contains the position
    for match in WORD_PATTERN.finditer(line):
        start, end = match.span()
        if start <= position.character <= end:
            return match.group()

    return None


class VBScriptLanguageServer:
    """VBScript Language Server implementation using pygls.

    This class wraps the pygls LanguageServer and provides VBScript-specific
    functionality including symbol parsing, indexing, and LSP feature handlers.
    """

    def __init__(self) -> None:
        """Initialize the VBScript Language Server."""
        self.lsp = LanguageServer(name="vbscript-lsp", version="1.0.0")
        self._parser = VBScriptParser()
        self._index = SymbolIndex()
        self._documents: dict[str, str] = {}

        # Register LSP feature handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register LSP protocol handlers."""

        @self.lsp.feature(types.TEXT_DOCUMENT_DID_OPEN)
        def did_open(params: types.DidOpenTextDocumentParams) -> None:
            """Handle document open event."""
            uri = params.text_document.uri
            content = params.text_document.text
            self._open_document(uri, content)

        @self.lsp.feature(types.TEXT_DOCUMENT_DID_CHANGE)
        def did_change(params: types.DidChangeTextDocumentParams) -> None:
            """Handle document change event."""
            uri = params.text_document.uri
            # For full sync, take the last change which contains the full content
            if params.content_changes:
                content = params.content_changes[-1].text
                self._change_document(uri, content)

        @self.lsp.feature(types.TEXT_DOCUMENT_DID_CLOSE)
        def did_close(params: types.DidCloseTextDocumentParams) -> None:
            """Handle document close event."""
            uri = params.text_document.uri
            self._close_document(uri)

        @self.lsp.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
        def document_symbol_handler(
            params: types.DocumentSymbolParams,
        ) -> list[types.DocumentSymbol] | None:
            """Handle document symbol request."""
            return self.document_symbol(params)

        @self.lsp.feature(types.TEXT_DOCUMENT_DEFINITION)
        def definition_handler(
            params: types.DefinitionParams,
        ) -> types.Location | list[types.Location] | None:
            """Handle go to definition request."""
            return self.goto_definition(params)

        @self.lsp.feature(types.TEXT_DOCUMENT_REFERENCES)
        def references_handler(
            params: types.ReferenceParams,
        ) -> list[types.Location] | None:
            """Handle find references request."""
            return self.find_references(params)

    def _open_document(self, uri: str, content: str) -> None:
        """Process a newly opened document.

        Args:
            uri: Document URI
            content: Document content
        """
        self._documents[uri] = content
        self._update_index(uri, content)

    def _change_document(self, uri: str, content: str) -> None:
        """Process a document change.

        Args:
            uri: Document URI
            content: New document content
        """
        self._documents[uri] = content
        self._update_index(uri, content)

    def _close_document(self, uri: str) -> None:
        """Process a closed document.

        Args:
            uri: Document URI
        """
        if uri in self._documents:
            del self._documents[uri]
        self._index.remove(uri)

    def _update_index(self, uri: str, content: str) -> None:
        """Parse document and update the symbol index.

        Args:
            uri: Document URI
            content: Document content
        """
        try:
            symbols = self._parser.parse(content, uri)
            self._index.update(uri, symbols)
        except Exception as e:
            logger.warning(f"Failed to parse document {uri}: {e}")

    def document_symbol(
        self, params: types.DocumentSymbolParams
    ) -> list[types.DocumentSymbol] | None:
        """Return document symbols for the given document.

        Args:
            params: Document symbol request parameters

        Returns:
            List of DocumentSymbol objects, or None if document not found
        """
        uri = params.text_document.uri
        content = self._documents.get(uri)

        if content is None:
            return None

        symbols = self._parser.parse(content, uri)
        return [s.to_document_symbol() for s in symbols]

    def goto_definition(
        self, params: types.DefinitionParams
    ) -> types.Location | list[types.Location] | None:
        """Find the definition of the symbol at the given position.

        Args:
            params: Definition request parameters

        Returns:
            Location of the definition, or None if not found
        """
        uri = params.text_document.uri
        content = self._documents.get(uri)

        if content is None:
            return None

        # Get the word at cursor position
        word = get_word_at_position(content, params.position)
        if word is None:
            return None

        # Find definition in index
        definition = self._index.find_definition(word)
        if definition is None:
            return None

        return types.Location(
            uri=definition.uri,
            range=types.Range(
                start=types.Position(
                    line=definition.start_line,
                    character=definition.start_character,
                ),
                end=types.Position(
                    line=definition.end_line,
                    character=definition.end_character,
                ),
            ),
        )

    def find_references(
        self, params: types.ReferenceParams
    ) -> list[types.Location] | None:
        """Find all references to the symbol at the given position.

        Args:
            params: Reference request parameters

        Returns:
            List of Location objects for each reference
        """
        uri = params.text_document.uri
        content = self._documents.get(uri)

        if content is None:
            return None

        # Get the word at cursor position
        word = get_word_at_position(content, params.position)
        if word is None:
            return None

        # Find references in index
        include_declaration = params.context.include_declaration
        return self._index.find_references(word, include_declaration)

    def start_io(self) -> None:
        """Start the server in STDIO mode."""
        self.lsp.start_io()


def main() -> None:
    """Entry point for the VBScript Language Server."""
    logging.basicConfig(level=logging.INFO)
    server = VBScriptLanguageServer()
    server.start_io()


if __name__ == "__main__":
    main()
