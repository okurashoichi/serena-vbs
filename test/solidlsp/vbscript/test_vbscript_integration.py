"""
Integration tests for VBScript Language Server.

These tests verify the LSP server works correctly with real VBScript/ASP files
and can perform end-to-end operations like document symbols, go-to-definition,
and find-references.
"""

from pathlib import Path

import pytest
from lsprotocol import types

from solidlsp.language_servers.vbscript_lsp.server import VBScriptLanguageServer
from solidlsp.ls_config import Language


# These marks will be applied to all tests in this module
pytestmark = [pytest.mark.vbscript]


class TestLSPServerIntegration:
    """Integration tests for VBScript LSP server startup and initialization."""

    @pytest.fixture
    def vbscript_test_repo_path(self) -> str:
        """Get the path to the VBScript test repository."""
        test_dir = Path(__file__).parent.parent.parent
        return str(test_dir / "resources" / "repos" / "vbscript" / "test_repo")

    @pytest.fixture
    def lsp_server(self) -> VBScriptLanguageServer:
        """Create and return a VBScript LSP server instance."""
        return VBScriptLanguageServer()

    def test_server_initialization(self, lsp_server: VBScriptLanguageServer) -> None:
        """Test that the LSP server initializes correctly."""
        assert lsp_server.lsp.name == "vbscript-lsp"
        assert lsp_server.lsp.version is not None

    def test_server_has_parser(self, lsp_server: VBScriptLanguageServer) -> None:
        """Test that the server has a parser instance."""
        assert lsp_server._parser is not None

    def test_server_has_index(self, lsp_server: VBScriptLanguageServer) -> None:
        """Test that the server has a symbol index."""
        assert lsp_server._index is not None


class TestDocumentSymbolIntegration:
    """Integration tests for textDocument/documentSymbol."""

    @pytest.fixture
    def vbscript_test_repo_path(self) -> str:
        """Get the path to the VBScript test repository."""
        test_dir = Path(__file__).parent.parent.parent
        return str(test_dir / "resources" / "repos" / "vbscript" / "test_repo")

    @pytest.fixture
    def lsp_server(self) -> VBScriptLanguageServer:
        """Create and return a VBScript LSP server instance."""
        return VBScriptLanguageServer()

    def test_document_symbol_vbs_file(
        self, lsp_server: VBScriptLanguageServer, vbscript_test_repo_path: str
    ) -> None:
        """Test document symbols for a .vbs file."""
        vbs_path = Path(vbscript_test_repo_path) / "utils.vbs"
        with open(vbs_path) as f:
            content = f.read()

        uri = vbs_path.as_uri()
        lsp_server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = lsp_server.document_symbol(params)

        assert result is not None
        assert len(result) > 0

        # Check for expected functions
        names = [s.name for s in result]
        assert "AddNumbers" in names
        assert "ShowMessage" in names

    def test_document_symbol_asp_file(
        self, lsp_server: VBScriptLanguageServer, vbscript_test_repo_path: str
    ) -> None:
        """Test document symbols for a .asp file."""
        asp_path = Path(vbscript_test_repo_path) / "default.asp"
        with open(asp_path) as f:
            content = f.read()

        uri = asp_path.as_uri()
        lsp_server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = lsp_server.document_symbol(params)

        assert result is not None
        assert len(result) > 0

        # Check for functions in ASP file
        names = [s.name for s in result]
        assert "GetFormattedDate" in names or "GetGreeting" in names

    def test_document_symbol_inc_file(
        self, lsp_server: VBScriptLanguageServer, vbscript_test_repo_path: str
    ) -> None:
        """Test document symbols for a .inc file."""
        inc_path = Path(vbscript_test_repo_path) / "database.inc"
        with open(inc_path) as f:
            content = f.read()

        uri = inc_path.as_uri()
        lsp_server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = lsp_server.document_symbol(params)

        assert result is not None
        assert len(result) > 0

        # Check for expected functions in include file
        names = [s.name for s in result]
        assert "GetConnectionString" in names or "ExecuteQuery" in names

    def test_document_symbol_class_file(
        self, lsp_server: VBScriptLanguageServer, vbscript_test_repo_path: str
    ) -> None:
        """Test document symbols for a file with class definitions."""
        cls_path = Path(vbscript_test_repo_path) / "classes.vbs"
        with open(cls_path) as f:
            content = f.read()

        uri = cls_path.as_uri()
        lsp_server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = lsp_server.document_symbol(params)

        assert result is not None
        # Should have class symbols
        class_symbols = [s for s in result if s.kind == types.SymbolKind.Class]
        assert len(class_symbols) > 0

        # Check for expected classes
        class_names = [s.name for s in class_symbols]
        assert "Person" in class_names or "Calculator" in class_names

    def test_document_symbol_property_file(
        self, lsp_server: VBScriptLanguageServer, vbscript_test_repo_path: str
    ) -> None:
        """Test document symbols for a file with Property definitions."""
        prop_path = Path(vbscript_test_repo_path) / "properties.vbs"
        with open(prop_path) as f:
            content = f.read()

        uri = prop_path.as_uri()
        lsp_server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = lsp_server.document_symbol(params)

        assert result is not None
        assert len(result) > 0


class TestGoToDefinitionIntegration:
    """Integration tests for textDocument/definition."""

    @pytest.fixture
    def lsp_server(self) -> VBScriptLanguageServer:
        """Create and return a VBScript LSP server instance."""
        return VBScriptLanguageServer()

    def test_goto_definition_function(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test go to definition for a function call."""
        content = """Function GetValue()
    GetValue = 42
End Function

Sub Main()
    x = GetValue()
End Sub
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        # Position cursor on "GetValue" in the call (line 5, character 8)
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=5, character=8),
        )
        result = lsp_server.goto_definition(params)

        assert result is not None
        if isinstance(result, list):
            location = result[0]
        else:
            location = result

        assert location.uri == uri
        assert location.range.start.line == 0  # Function definition line

    def test_goto_definition_class_method(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test go to definition for a class method."""
        content = """Class MyClass
    Public Function GetValue()
        GetValue = 1
    End Function
End Class

Sub Main()
    Dim obj
    x = obj.GetValue()
End Sub
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        # Should find GetValue definition in class
        definition = lsp_server._index.find_definition("GetValue")
        assert definition is not None
        assert definition.name == "GetValue"

    def test_goto_definition_not_found(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test go to definition when symbol is not found."""
        content = """Sub Main()
    x = UnknownFunction()
End Sub
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=1, character=10),
        )
        result = lsp_server.goto_definition(params)

        assert result is None


class TestFindReferencesIntegration:
    """Integration tests for textDocument/references."""

    @pytest.fixture
    def lsp_server(self) -> VBScriptLanguageServer:
        """Create and return a VBScript LSP server instance."""
        return VBScriptLanguageServer()

    def test_find_references_with_declaration(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test find references including declaration."""
        content = """Function Helper()
    Helper = 1
End Function
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=0, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = lsp_server.find_references(params)

        assert result is not None
        assert len(result) >= 1

    def test_find_references_cross_document(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test find references across multiple documents."""
        # Open first document with function definition
        content1 = """Function Helper()
    Helper = 1
End Function
"""
        uri1 = "file:///file1.vbs"
        lsp_server._open_document(uri1, content1)

        # Open second document that calls the function
        content2 = """Sub Main()
    x = Helper()
End Sub
"""
        uri2 = "file:///file2.vbs"
        lsp_server._open_document(uri2, content2)

        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=uri1),
            position=types.Position(line=0, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = lsp_server.find_references(params)

        # Should find references in both documents
        assert result is not None
        assert len(result) >= 2
        uris = [loc.uri for loc in result]
        assert uri1 in uris
        assert uri2 in uris

    def test_find_references_without_declaration(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test find references excluding declaration."""
        content = """Function GetValue()
    GetValue = 42
End Function

Sub Main()
    x = GetValue()
    y = GetValue()
End Sub
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=0, character=10),
            context=types.ReferenceContext(include_declaration=False),
        )
        result = lsp_server.find_references(params)

        # Should find references but not the definition
        assert result is not None
        # Should have at least the calls (line 5, 6)
        assert len(result) >= 1
        # None of the results should be on the definition line
        for loc in result:
            # Definition is on line 0
            assert not (loc.range.start.line == 0 and loc.range.start.character < 15)

    def test_find_references_case_insensitive(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test that find references is case-insensitive."""
        content = """Function MyFunc()
End Function

Sub Main()
    MyFunc
    MYFUNC
    myfunc
End Sub
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=0, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = lsp_server.find_references(params)

        # Should find all case variations
        assert result is not None
        assert len(result) >= 4  # definition + 3 calls

    def test_find_references_excludes_comments(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test that references in comments are excluded."""
        content = """Function GetValue()
End Function

Sub Main()
    ' GetValue is a helper function
    x = GetValue()
End Sub
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=0, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = lsp_server.find_references(params)

        # Should NOT include the commented reference (line 4)
        assert result is not None
        for loc in result:
            if loc.range.start.line == 4:
                # Line 4 is the comment line
                pytest.fail("Found reference in comment")

    def test_find_references_excludes_strings(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test that references in string literals are excluded."""
        content = """Function GetValue()
End Function

Sub Main()
    msg = "Call GetValue to get data"
    x = GetValue()
End Sub
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=0, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = lsp_server.find_references(params)

        # Should NOT include the string literal reference
        assert result is not None
        for loc in result:
            if loc.range.start.line == 4:
                # Check if it's inside the string
                if loc.range.start.character > 10:  # After 'msg = "'
                    pytest.fail("Found reference in string literal")

    def test_find_references_not_found(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test that find references returns empty list for unknown symbol."""
        content = """Sub Main()
    x = 1
End Sub
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        # Position cursor on whitespace where no word exists
        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=0, character=30),  # Beyond end of line
            context=types.ReferenceContext(include_declaration=True),
        )
        result = lsp_server.find_references(params)

        # No word at position, so result should be None
        assert result is None


class TestSerenaIntegration:
    """Integration tests for Serena integration."""

    def test_vbscript_language_enum_exists(self) -> None:
        """Test that VBSCRIPT is in the Language enum."""
        assert hasattr(Language, "VBSCRIPT")
        assert Language.VBSCRIPT.value == "vbscript"

    def test_file_extension_matching_vbs(self) -> None:
        """Test that .vbs files are recognized."""
        matcher = Language.VBSCRIPT.get_source_fn_matcher()
        assert matcher.is_relevant_filename("script.vbs")
        assert matcher.is_relevant_filename("path/to/script.vbs")
        assert matcher.is_relevant_filename("script.VBS")

    def test_file_extension_matching_asp(self) -> None:
        """Test that .asp files are recognized."""
        matcher = Language.VBSCRIPT.get_source_fn_matcher()
        assert matcher.is_relevant_filename("page.asp")
        assert matcher.is_relevant_filename("path/to/page.asp")
        assert matcher.is_relevant_filename("page.ASP")

    def test_file_extension_matching_inc(self) -> None:
        """Test that .inc files are recognized."""
        matcher = Language.VBSCRIPT.get_source_fn_matcher()
        assert matcher.is_relevant_filename("include.inc")
        assert matcher.is_relevant_filename("path/to/include.inc")
        assert matcher.is_relevant_filename("include.INC")

    def test_file_extension_not_matching_other(self) -> None:
        """Test that other files are not recognized."""
        matcher = Language.VBSCRIPT.get_source_fn_matcher()
        assert not matcher.is_relevant_filename("script.py")
        assert not matcher.is_relevant_filename("script.js")
        assert not matcher.is_relevant_filename("script.vb")  # VB.NET

    def test_get_ls_class_returns_correct_class(self) -> None:
        """Test that get_ls_class returns VBScriptLanguageServer."""
        from solidlsp.language_servers.vbscript_language_server import (
            VBScriptLanguageServer as SerenaVBScriptLS,
        )

        ls_class = Language.VBSCRIPT.get_ls_class()
        assert ls_class is SerenaVBScriptLS

    def test_from_ls_class_returns_vbscript(self) -> None:
        """Test that from_ls_class returns VBSCRIPT."""
        from solidlsp.language_servers.vbscript_language_server import (
            VBScriptLanguageServer as SerenaVBScriptLS,
        )

        lang = Language.from_ls_class(SerenaVBScriptLS)
        assert lang is Language.VBSCRIPT


class TestErrorHandling:
    """Integration tests for error handling."""

    @pytest.fixture
    def lsp_server(self) -> VBScriptLanguageServer:
        """Create and return a VBScript LSP server instance."""
        return VBScriptLanguageServer()

    def test_invalid_document_uri(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test handling of invalid document URI."""
        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri="file:///nonexistent.vbs")
        )
        result = lsp_server.document_symbol(params)

        # Should return None for unknown document
        assert result is None

    def test_malformed_vbscript(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test handling of malformed VBScript."""
        content = """Function Incomplete(
    ' Missing End Function
"""
        uri = "file:///malformed.vbs"
        lsp_server._open_document(uri, content)

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        # Should not crash
        result = lsp_server.document_symbol(params)
        # May or may not find symbols, but should not crash
        assert result is not None or result is None

    def test_empty_document(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test handling of empty document."""
        uri = "file:///empty.vbs"
        lsp_server._open_document(uri, "")

        params = types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
        result = lsp_server.document_symbol(params)

        # Should return empty list for empty document
        assert result is not None
        assert len(result) == 0

    def test_document_close_removes_from_index(
        self, lsp_server: VBScriptLanguageServer
    ) -> None:
        """Test that closing a document removes it from the index."""
        content = """Function TestFunc()
End Function
"""
        uri = "file:///test.vbs"
        lsp_server._open_document(uri, content)

        # Verify function is indexed
        assert lsp_server._index.find_definition("TestFunc") is not None

        # Close document
        lsp_server._close_document(uri)

        # Verify function is removed from index
        assert lsp_server._index.find_definition("TestFunc") is None
