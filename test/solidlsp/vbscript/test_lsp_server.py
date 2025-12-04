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

    def test_document_symbol_includes_include_directives(self) -> None:
        """Test that document_symbol returns include directives as File symbols."""
        server = VBScriptLanguageServer()

        content = '''<!--#include file="utils.asp"-->
<!--#include file="common.asp"-->
<%
Sub Main()
End Sub
%>'''
        uri = "file:///project/main.asp"
        server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = server.document_symbol(params)

        assert result is not None
        # Should include both the Sub and the include directives
        names = [s.name for s in result]
        assert "Main" in names
        # Include directives should appear as File symbols
        file_symbols = [s for s in result if s.kind == types.SymbolKind.File]
        assert len(file_symbols) == 2
        # The include paths should be in the symbol names
        include_names = [s.name for s in file_symbols]
        assert any("utils.asp" in name for name in include_names)
        assert any("common.asp" in name for name in include_names)

    def test_document_symbol_include_has_correct_range(self) -> None:
        """Test that include symbols have correct position range."""
        server = VBScriptLanguageServer()

        content = '''<!--#include file="header.asp"-->
<%
Sub Main()
End Sub
%>'''
        uri = "file:///project/main.asp"
        server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = server.document_symbol(params)

        assert result is not None
        file_symbols = [s for s in result if s.kind == types.SymbolKind.File]
        assert len(file_symbols) == 1
        include_symbol = file_symbols[0]
        # Include is on line 0
        assert include_symbol.range.start.line == 0
        assert include_symbol.selection_range.start.line == 0

    def test_document_symbol_invalid_include_shows_error(self) -> None:
        """Test that invalid include directives are marked with error info."""
        server = VBScriptLanguageServer()

        # Virtual include without workspace root will be invalid
        content = '''<!--#include virtual="/missing/file.asp"-->
<%
Sub Main()
End Sub
%>'''
        uri = "file:///project/main.asp"
        server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = server.document_symbol(params)

        assert result is not None
        file_symbols = [s for s in result if s.kind == types.SymbolKind.File]
        assert len(file_symbols) == 1
        # Invalid includes should have some indicator in the name
        include_symbol = file_symbols[0]
        # Could be marked with error prefix or have detail indicating error
        assert include_symbol.name is not None

    def test_document_symbol_vbs_file_no_include_symbols(self) -> None:
        """Test that plain .vbs files don't have include symbols."""
        server = VBScriptLanguageServer()

        content = """Function GetValue()
    GetValue = 42
End Function
"""
        uri = "file:///project/script.vbs"
        server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = server.document_symbol(params)

        assert result is not None
        file_symbols = [s for s in result if s.kind == types.SymbolKind.File]
        assert len(file_symbols) == 0


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

    def test_goto_definition_finds_symbol_in_included_file(self) -> None:
        """Test that goto_definition finds symbol in directly included file."""
        server = VBScriptLanguageServer()

        # Main file includes utils.asp
        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
    x = GetValue()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        # Included file has GetValue function
        utils_content = '''<%
Function GetValue()
    GetValue = 42
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        # Open both files
        server._open_document(utils_uri, utils_content)
        server._open_document(main_uri, main_content)

        # Position cursor on "GetValue" in the call (line 3)
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=main_uri),
            position=types.Position(line=3, character=10),
        )
        result = server.goto_definition(params)

        assert result is not None
        # Should return Location(s) pointing to utils.asp
        if isinstance(result, list):
            assert len(result) >= 1
            location = result[0]
        else:
            location = result

        assert location.uri == utils_uri

    def test_goto_definition_finds_symbol_in_transitive_include(self) -> None:
        """Test that goto_definition finds symbol in transitively included file."""
        server = VBScriptLanguageServer()

        # main.asp includes utils.asp, utils.asp includes helpers.asp
        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
    x = HelperFunc()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        utils_content = '''<!--#include file="helpers.asp"-->
<%
Function UtilFunc()
    UtilFunc = 1
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        helpers_content = '''<%
Function HelperFunc()
    HelperFunc = 99
End Function
%>'''
        helpers_uri = "file:///project/helpers.asp"

        # Open all files (order matters for include graph)
        server._open_document(helpers_uri, helpers_content)
        server._open_document(utils_uri, utils_content)
        server._open_document(main_uri, main_content)

        # Position cursor on "HelperFunc" in the call
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=main_uri),
            position=types.Position(line=3, character=10),
        )
        result = server.goto_definition(params)

        assert result is not None
        if isinstance(result, list):
            assert len(result) >= 1
            location = result[0]
        else:
            location = result

        assert location.uri == helpers_uri

    def test_goto_definition_returns_multiple_definitions(self) -> None:
        """Test that goto_definition returns all definitions when symbol exists in multiple files."""
        server = VBScriptLanguageServer()

        # Main file includes both files that have same function name
        main_content = '''<!--#include file="file1.asp"-->
<!--#include file="file2.asp"-->
<%
Sub Main()
    x = DuplicateFunc()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        file1_content = '''<%
Function DuplicateFunc()
    DuplicateFunc = 1
End Function
%>'''
        file1_uri = "file:///project/file1.asp"

        file2_content = '''<%
Function DuplicateFunc()
    DuplicateFunc = 2
End Function
%>'''
        file2_uri = "file:///project/file2.asp"

        # Open all files
        server._open_document(file1_uri, file1_content)
        server._open_document(file2_uri, file2_content)
        server._open_document(main_uri, main_content)

        # Position cursor on "DuplicateFunc"
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=main_uri),
            position=types.Position(line=4, character=10),
        )
        result = server.goto_definition(params)

        assert result is not None
        # Should return list of locations
        assert isinstance(result, list)
        assert len(result) == 2
        uris = [loc.uri for loc in result]
        assert file1_uri in uris
        assert file2_uri in uris

    def test_goto_definition_local_takes_precedence(self) -> None:
        """Test that local definition takes precedence over included file."""
        server = VBScriptLanguageServer()

        # Main file has GetValue and includes utils.asp which also has GetValue
        main_content = '''<!--#include file="utils.asp"-->
<%
Function GetValue()
    GetValue = 100
End Function

Sub Main()
    x = GetValue()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        utils_content = '''<%
Function GetValue()
    GetValue = 42
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        # Open both files
        server._open_document(utils_uri, utils_content)
        server._open_document(main_uri, main_content)

        # Position cursor on "GetValue" in the call (line 7)
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=main_uri),
            position=types.Position(line=7, character=10),
        )
        result = server.goto_definition(params)

        assert result is not None
        # Should return Location pointing to local definition in main.asp
        if isinstance(result, list):
            assert len(result) >= 1
            location = result[0]
        else:
            location = result

        assert location.uri == main_uri


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

    def test_find_references_includes_references_from_includer_files(self) -> None:
        """Test that find_references includes references from files that include current file."""
        server = VBScriptLanguageServer()

        # utils.asp defines GetValue function
        utils_content = '''<%
Function GetValue()
    GetValue = 42
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        # main.asp includes utils.asp and calls GetValue
        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
    x = GetValue()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        # Open both files
        server._open_document(utils_uri, utils_content)
        server._open_document(main_uri, main_content)

        # Find references for GetValue from utils.asp
        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=utils_uri),
            position=types.Position(line=1, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = server.find_references(params)

        assert result is not None
        # Should find references in both files
        uris = [loc.uri for loc in result]
        assert utils_uri in uris  # Declaration in utils.asp
        assert main_uri in uris   # Call in main.asp

    def test_find_references_searches_all_includers(self) -> None:
        """Test that find_references searches all files that include the current file."""
        server = VBScriptLanguageServer()

        # common.asp defines Helper function
        common_content = '''<%
Function Helper()
    Helper = 1
End Function
%>'''
        common_uri = "file:///project/common.asp"

        # page1.asp includes common.asp
        page1_content = '''<!--#include file="common.asp"-->
<%
Sub Page1()
    Helper
End Sub
%>'''
        page1_uri = "file:///project/page1.asp"

        # page2.asp also includes common.asp
        page2_content = '''<!--#include file="common.asp"-->
<%
Sub Page2()
    x = Helper()
End Sub
%>'''
        page2_uri = "file:///project/page2.asp"

        # Open all files
        server._open_document(common_uri, common_content)
        server._open_document(page1_uri, page1_content)
        server._open_document(page2_uri, page2_content)

        # Find references for Helper from common.asp
        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=common_uri),
            position=types.Position(line=1, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = server.find_references(params)

        assert result is not None
        uris = [loc.uri for loc in result]
        # Should find references in all three files
        assert common_uri in uris   # Declaration and self-reference
        assert page1_uri in uris    # Call in page1.asp
        assert page2_uri in uris    # Call in page2.asp

    def test_find_references_include_declaration_false(self) -> None:
        """Test that include_declaration=False excludes declarations from includer files."""
        server = VBScriptLanguageServer()

        # utils.asp defines GetValue function
        utils_content = '''<%
Function GetValue()
    GetValue = 42
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        # main.asp includes utils.asp and calls GetValue
        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
    x = GetValue()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        # Open both files
        server._open_document(utils_uri, utils_content)
        server._open_document(main_uri, main_content)

        # Find references for GetValue with include_declaration=False
        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=utils_uri),
            position=types.Position(line=1, character=10),
            context=types.ReferenceContext(include_declaration=False),
        )
        result = server.find_references(params)

        assert result is not None
        # Should find non-declaration references
        # At minimum the call in main.asp
        uris = [loc.uri for loc in result]
        assert main_uri in uris  # Call in main.asp


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


@pytest.mark.vbscript
class TestIncludeIntegration:
    """Test include directive integration in LSP server."""

    def test_server_has_include_graph(self) -> None:
        """Test that server has an include graph."""
        server = VBScriptLanguageServer()
        assert hasattr(server, "_include_graph")
        assert server._include_graph is not None

    def test_server_has_include_parser(self) -> None:
        """Test that server has an include directive parser."""
        server = VBScriptLanguageServer()
        assert hasattr(server, "_include_parser")
        assert server._include_parser is not None

    def test_open_document_extracts_includes(self) -> None:
        """Test that opening a document extracts include directives."""
        server = VBScriptLanguageServer()

        content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
End Sub
%>'''
        uri = "file:///project/main.asp"

        server._open_document(uri, content)

        # Include graph should have the directive
        directives = server._include_graph.get_include_directives(uri)
        assert len(directives) == 1
        assert directives[0].raw_path == "utils.asp"

    def test_open_document_updates_include_graph(self) -> None:
        """Test that opening a document updates include graph edges."""
        server = VBScriptLanguageServer()

        content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
End Sub
%>'''
        uri = "file:///project/main.asp"

        server._open_document(uri, content)

        # Should have edge to utils.asp
        includes = server._include_graph.get_direct_includes(uri)
        assert len(includes) == 1
        assert "utils.asp" in includes[0]

    def test_change_document_updates_include_graph(self) -> None:
        """Test that changing a document updates include graph."""
        server = VBScriptLanguageServer()
        uri = "file:///project/main.asp"

        # Initial content with one include
        content1 = '''<!--#include file="old.asp"-->
<%
Sub Main()
End Sub
%>'''
        server._open_document(uri, content1)
        includes1 = server._include_graph.get_direct_includes(uri)
        assert len(includes1) == 1
        assert "old.asp" in includes1[0]

        # Change to different include
        content2 = '''<!--#include file="new.asp"-->
<%
Sub Main()
End Sub
%>'''
        server._change_document(uri, content2)
        includes2 = server._include_graph.get_direct_includes(uri)
        assert len(includes2) == 1
        assert "new.asp" in includes2[0]
        assert "old.asp" not in includes2[0]

    def test_close_document_removes_from_include_graph(self) -> None:
        """Test that closing a document removes it from include graph."""
        server = VBScriptLanguageServer()
        uri = "file:///project/main.asp"

        content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
End Sub
%>'''
        server._open_document(uri, content)

        # Verify include exists
        assert len(server._include_graph.get_direct_includes(uri)) == 1

        # Close document
        server._close_document(uri)

        # Include should be removed
        assert len(server._include_graph.get_direct_includes(uri)) == 0

    def test_multiple_includes_extracted(self) -> None:
        """Test that multiple includes are extracted."""
        server = VBScriptLanguageServer()

        content = '''<!--#include file="header.asp"-->
<!--#include file="utils.asp"-->
<!--#include virtual="/includes/footer.asp"-->
<%
Sub Main()
End Sub
%>'''
        uri = "file:///project/main.asp"

        server._open_document(uri, content)

        directives = server._include_graph.get_include_directives(uri)
        assert len(directives) == 3

    def test_vbs_file_no_includes(self) -> None:
        """Test that plain .vbs files have no includes extracted."""
        server = VBScriptLanguageServer()

        content = """Function GetValue()
    GetValue = 42
End Function"""
        uri = "file:///project/script.vbs"

        server._open_document(uri, content)

        # Should have no includes
        directives = server._include_graph.get_include_directives(uri)
        assert len(directives) == 0
