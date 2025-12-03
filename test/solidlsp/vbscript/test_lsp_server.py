"""
Unit tests for VBScript LSP Server.

Tests the pygls-based LSP server implementation.
"""

import pytest
from lsprotocol import types

from solidlsp.language_servers.vbscript_lsp.server import (
    VBScriptLanguageServer,
    get_word_at_position,
)


@pytest.mark.vbscript
class TestVBScriptLanguageServer:
    """Test VBScript Language Server initialization."""

    def test_server_has_name(self) -> None:
        """Test that server has a name."""
        server = VBScriptLanguageServer()
        assert server.lsp.name == "vbscript-lsp"

    def test_server_has_version(self) -> None:
        """Test that server has a version."""
        server = VBScriptLanguageServer()
        assert server.lsp.version is not None


@pytest.mark.vbscript
class TestGetWordAtPosition:
    """Test word extraction at cursor position."""

    def test_get_word_at_start_of_line(self) -> None:
        """Test getting word at the start of a line."""
        content = "Function GetValue()\nEnd Function"
        # Position at "F" in "Function"
        position = types.Position(line=0, character=0)

        word = get_word_at_position(content, position)

        assert word == "Function"

    def test_get_word_in_middle_of_line(self) -> None:
        """Test getting word in the middle of a line."""
        content = "Function GetValue()\nEnd Function"
        # Position somewhere in "GetValue"
        position = types.Position(line=0, character=12)

        word = get_word_at_position(content, position)

        assert word == "GetValue"

    def test_get_word_at_end_of_word(self) -> None:
        """Test getting word when cursor is at end of word."""
        content = "Dim myVariable"
        # Position at end of "myVariable" (character 14)
        position = types.Position(line=0, character=14)

        word = get_word_at_position(content, position)

        assert word == "myVariable"

    def test_get_word_returns_none_on_whitespace(self) -> None:
        """Test that None is returned when cursor is on whitespace."""
        content = "Function   GetValue()"
        # Position on whitespace between Function and GetValue
        position = types.Position(line=0, character=9)

        word = get_word_at_position(content, position)

        assert word is None

    def test_get_word_returns_none_on_operator(self) -> None:
        """Test that None is returned when cursor is on an operator."""
        content = "x = y + z"
        # Position on "="
        position = types.Position(line=0, character=2)

        word = get_word_at_position(content, position)

        assert word is None

    def test_get_word_with_underscore(self) -> None:
        """Test that words with underscores are extracted correctly."""
        content = "Dim my_variable"
        # Position in "my_variable"
        position = types.Position(line=0, character=6)

        word = get_word_at_position(content, position)

        assert word == "my_variable"

    def test_get_word_multiline(self) -> None:
        """Test getting word on a specific line in multiline content."""
        content = "Line1\nFunction TestFunc()\nEnd Function"
        # Position at "TestFunc" on line 1
        position = types.Position(line=1, character=12)

        word = get_word_at_position(content, position)

        assert word == "TestFunc"

    def test_get_word_invalid_line(self) -> None:
        """Test behavior when line number is out of range."""
        content = "Single line"
        position = types.Position(line=5, character=0)

        word = get_word_at_position(content, position)

        assert word is None


@pytest.mark.vbscript
class TestDocumentSymbolHandler:
    """Test document symbol handler."""

    def test_document_symbol_returns_symbols(self) -> None:
        """Test that document_symbol returns parsed symbols."""
        server = VBScriptLanguageServer()

        # Simulate opening a document
        content = """Function GetValue()
    GetValue = 42
End Function

Sub DoSomething()
End Sub
"""
        uri = "file:///test.vbs"
        server._open_document(uri, content)

        # Request document symbols
        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = server.document_symbol(params)

        assert result is not None
        assert len(result) == 2
        names = [s.name for s in result]
        assert "GetValue" in names
        assert "DoSomething" in names

    def test_document_symbol_with_class(self) -> None:
        """Test document symbols with class and members."""
        server = VBScriptLanguageServer()

        content = """Class MyClass
    Public Function GetValue()
        GetValue = 1
    End Function
End Class
"""
        uri = "file:///class.vbs"
        server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = server.document_symbol(params)

        assert result is not None
        assert len(result) == 1
        assert result[0].name == "MyClass"
        assert result[0].children is not None
        assert len(result[0].children) == 1
        assert result[0].children[0].name == "GetValue"


@pytest.mark.vbscript
class TestDefinitionHandler:
    """Test go to definition handler."""

    def test_goto_definition_finds_function(self) -> None:
        """Test that goto_definition finds a function definition."""
        server = VBScriptLanguageServer()

        content = """Function GetValue()
    GetValue = 42
End Function

Sub Main()
    x = GetValue()
End Sub
"""
        uri = "file:///test.vbs"
        server._open_document(uri, content)

        # Position cursor on "GetValue" in the call (line 5, ~8 chars in)
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=5, character=8),
        )
        result = server.goto_definition(params)

        assert result is not None
        # Should return Location pointing to function definition
        if isinstance(result, list):
            assert len(result) == 1
            location = result[0]
        else:
            location = result

        assert location.uri == uri
        assert location.range.start.line == 0  # Function is on line 0

    def test_goto_definition_not_found(self) -> None:
        """Test that goto_definition returns None for unknown symbol."""
        server = VBScriptLanguageServer()

        content = """Sub Main()
    x = UnknownFunc()
End Sub
"""
        uri = "file:///test.vbs"
        server._open_document(uri, content)

        # Position cursor on "UnknownFunc"
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=1, character=10),
        )
        result = server.goto_definition(params)

        assert result is None


@pytest.mark.vbscript
class TestReferencesHandler:
    """Test find references handler."""

    def test_find_references_returns_locations(self) -> None:
        """Test that find_references returns symbol locations."""
        server = VBScriptLanguageServer()

        content = """Function Helper()
    Helper = 1
End Function
"""
        uri = "file:///test.vbs"
        server._open_document(uri, content)

        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=0, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = server.find_references(params)

        assert result is not None
        assert len(result) >= 1


@pytest.mark.vbscript
class TestDocumentLifecycle:
    """Test document open/change/close lifecycle."""

    def test_open_document_indexes_symbols(self) -> None:
        """Test that opening a document indexes its symbols."""
        server = VBScriptLanguageServer()

        content = "Function TestFunc()\nEnd Function"
        uri = "file:///test.vbs"

        server._open_document(uri, content)

        # Symbol should be findable
        definition = server._index.find_definition("TestFunc")
        assert definition is not None

    def test_change_document_updates_index(self) -> None:
        """Test that changing a document updates the index."""
        server = VBScriptLanguageServer()

        # Initial content
        uri = "file:///test.vbs"
        server._open_document(uri, "Function OldFunc()\nEnd Function")

        assert server._index.find_definition("OldFunc") is not None
        assert server._index.find_definition("NewFunc") is None

        # Change content
        server._change_document(uri, "Function NewFunc()\nEnd Function")

        assert server._index.find_definition("OldFunc") is None
        assert server._index.find_definition("NewFunc") is not None

    def test_close_document_removes_from_index(self) -> None:
        """Test that closing a document removes symbols from index."""
        server = VBScriptLanguageServer()

        uri = "file:///test.vbs"
        server._open_document(uri, "Function TestFunc()\nEnd Function")

        assert server._index.find_definition("TestFunc") is not None

        server._close_document(uri)

        assert server._index.find_definition("TestFunc") is None
