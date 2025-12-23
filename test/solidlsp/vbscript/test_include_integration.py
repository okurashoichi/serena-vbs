"""
Integration tests for VBScript Include Reference Tracking.

These tests verify end-to-end functionality of include directive handling,
including multi-file scenarios, transitive includes, and circular references.
"""

import pytest
from lsprotocol import types

from solidlsp.language_servers.vbscript_lsp.server import VBScriptLanguageServer


# =============================================================================
# Task 10.1: Test file configurations
# =============================================================================


@pytest.mark.vbscript
class TestIncludeFileConfigurations:
    """Test various include file configurations."""

    def test_chain_include_a_to_b_to_c(self) -> None:
        """Test A includes B, B includes C chain configuration."""
        server = VBScriptLanguageServer()

        # File C: Base utility
        c_content = '''<%
Function BaseHelper()
    BaseHelper = 1
End Function
%>'''
        c_uri = "file:///project/c.asp"

        # File B: Middle layer, includes C
        b_content = '''<!--#include file="c.asp"-->
<%
Function MiddleFunc()
    x = BaseHelper()
    MiddleFunc = x
End Function
%>'''
        b_uri = "file:///project/b.asp"

        # File A: Top layer, includes B
        a_content = '''<!--#include file="b.asp"-->
<%
Sub TopLevel()
    y = MiddleFunc()
    z = BaseHelper()
End Sub
%>'''
        a_uri = "file:///project/a.asp"

        # Open files in order (C -> B -> A)
        server._open_document(c_uri, c_content)
        server._open_document(b_uri, b_content)
        server._open_document(a_uri, a_content)

        # Verify include graph structure
        direct_includes_a = server._include_graph.get_direct_includes(a_uri)
        assert len(direct_includes_a) == 1
        assert b_uri in direct_includes_a

        direct_includes_b = server._include_graph.get_direct_includes(b_uri)
        assert len(direct_includes_b) == 1
        assert c_uri in direct_includes_b

        # Verify transitive includes from A
        transitive = server._include_graph.get_transitive_includes(a_uri)
        assert b_uri in transitive
        assert c_uri in transitive

    def test_circular_reference_a_includes_b_includes_a(self) -> None:
        """Test circular reference: A includes B, B includes A."""
        server = VBScriptLanguageServer()

        # File A includes B
        a_content = '''<!--#include file="b.asp"-->
<%
Function FuncA()
    FuncA = 1
End Function
%>'''
        a_uri = "file:///project/a.asp"

        # File B includes A
        b_content = '''<!--#include file="a.asp"-->
<%
Function FuncB()
    FuncB = 2
End Function
%>'''
        b_uri = "file:///project/b.asp"

        # Open both files
        server._open_document(a_uri, a_content)
        server._open_document(b_uri, b_content)

        # Should detect cycle
        assert server._include_graph.has_cycle(a_uri)
        assert server._include_graph.has_cycle(b_uri)

        # Should still be able to get includes without infinite loop
        transitive_a = server._include_graph.get_transitive_includes(a_uri)
        assert b_uri in transitive_a

    def test_inc_file_extension(self) -> None:
        """Test .inc file extension is handled correctly."""
        server = VBScriptLanguageServer()

        # Helper functions in .inc file
        inc_content = '''<%
Function SharedHelper()
    SharedHelper = "shared"
End Function
%>'''
        inc_uri = "file:///project/includes/common.inc"

        # Main file includes .inc file
        main_content = '''<!--#include file="includes/common.inc"-->
<%
Sub Main()
    x = SharedHelper()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        server._open_document(inc_uri, inc_content)
        server._open_document(main_uri, main_content)

        # Verify include is recognized
        includes = server._include_graph.get_direct_includes(main_uri)
        assert len(includes) == 1
        assert "common.inc" in includes[0]

    def test_multiple_files_include_same_file(self) -> None:
        """Test multiple files including the same file."""
        server = VBScriptLanguageServer()

        # Shared utility file
        shared_content = '''<%
Function SharedFunc()
    SharedFunc = 100
End Function
%>'''
        shared_uri = "file:///project/shared.asp"

        # Page 1 includes shared
        page1_content = '''<!--#include file="shared.asp"-->
<%
Sub Page1()
    SharedFunc
End Sub
%>'''
        page1_uri = "file:///project/page1.asp"

        # Page 2 also includes shared
        page2_content = '''<!--#include file="shared.asp"-->
<%
Sub Page2()
    x = SharedFunc()
End Sub
%>'''
        page2_uri = "file:///project/page2.asp"

        server._open_document(shared_uri, shared_content)
        server._open_document(page1_uri, page1_content)
        server._open_document(page2_uri, page2_content)

        # Both pages should include shared
        assert shared_uri in server._include_graph.get_direct_includes(page1_uri)
        assert shared_uri in server._include_graph.get_direct_includes(page2_uri)

        # Shared should be included by both pages
        includers = server._include_graph.get_includers(shared_uri)
        assert page1_uri in includers
        assert page2_uri in includers


# =============================================================================
# Task 10.2: Integration tests for definition search via includes
# =============================================================================


@pytest.mark.vbscript
class TestIncludeDefinitionSearchIntegration:
    """Integration tests for Go to Definition across include relationships."""

    def test_goto_definition_direct_include(self) -> None:
        """Test goto definition finds symbol in directly included file."""
        server = VBScriptLanguageServer()

        utils_content = '''<%
Function UtilityFunc()
    UtilityFunc = 42
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
    x = UtilityFunc()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        server._open_document(utils_uri, utils_content)
        server._open_document(main_uri, main_content)

        # Find definition of UtilityFunc from main.asp
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=main_uri),
            position=types.Position(line=3, character=10),
        )
        result = server.goto_definition(params)

        assert result is not None
        if isinstance(result, list):
            location = result[0]
        else:
            location = result
        assert location.uri == utils_uri

    def test_goto_definition_nested_include(self) -> None:
        """Test goto definition finds symbol in nested include (A->B->C)."""
        server = VBScriptLanguageServer()

        # C has the function
        c_content = '''<%
Function DeepFunc()
    DeepFunc = "deep"
End Function
%>'''
        c_uri = "file:///project/c.asp"

        # B includes C
        b_content = '''<!--#include file="c.asp"-->
<%
Function BFunc()
    BFunc = 1
End Function
%>'''
        b_uri = "file:///project/b.asp"

        # A includes B, calls DeepFunc
        a_content = '''<!--#include file="b.asp"-->
<%
Sub AMain()
    x = DeepFunc()
End Sub
%>'''
        a_uri = "file:///project/a.asp"

        server._open_document(c_uri, c_content)
        server._open_document(b_uri, b_content)
        server._open_document(a_uri, a_content)

        # Find definition of DeepFunc from A
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=a_uri),
            position=types.Position(line=3, character=10),
        )
        result = server.goto_definition(params)

        assert result is not None
        if isinstance(result, list):
            location = result[0]
        else:
            location = result
        assert location.uri == c_uri

    def test_goto_definition_same_name_multiple_files(self) -> None:
        """Test goto definition with same function name in multiple files."""
        server = VBScriptLanguageServer()

        # File 1 has GetValue
        file1_content = '''<%
Function GetValue()
    GetValue = 1
End Function
%>'''
        file1_uri = "file:///project/file1.asp"

        # File 2 also has GetValue
        file2_content = '''<%
Function GetValue()
    GetValue = 2
End Function
%>'''
        file2_uri = "file:///project/file2.asp"

        # Main includes both
        main_content = '''<!--#include file="file1.asp"-->
<!--#include file="file2.asp"-->
<%
Sub Main()
    x = GetValue()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        server._open_document(file1_uri, file1_content)
        server._open_document(file2_uri, file2_content)
        server._open_document(main_uri, main_content)

        # Find definition - should return multiple locations
        params = types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=main_uri),
            position=types.Position(line=4, character=10),
        )
        result = server.goto_definition(params)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2
        uris = [loc.uri for loc in result]
        assert file1_uri in uris
        assert file2_uri in uris


# =============================================================================
# Task 10.3: Integration tests for reference search via includes
# =============================================================================


@pytest.mark.vbscript
class TestIncludeReferenceSearchIntegration:
    """Integration tests for Find References across include relationships."""

    def test_find_references_from_included_file(self) -> None:
        """Test find references from the included file finds references in includers."""
        server = VBScriptLanguageServer()

        # Library file
        lib_content = '''<%
Function LibFunc()
    LibFunc = 1
End Function
%>'''
        lib_uri = "file:///project/lib.asp"

        # Consumer 1
        consumer1_content = '''<!--#include file="lib.asp"-->
<%
Sub Consumer1()
    LibFunc
End Sub
%>'''
        consumer1_uri = "file:///project/consumer1.asp"

        # Consumer 2
        consumer2_content = '''<!--#include file="lib.asp"-->
<%
Sub Consumer2()
    x = LibFunc()
End Sub
%>'''
        consumer2_uri = "file:///project/consumer2.asp"

        server._open_document(lib_uri, lib_content)
        server._open_document(consumer1_uri, consumer1_content)
        server._open_document(consumer2_uri, consumer2_content)

        # Find references to LibFunc from lib.asp
        params = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=lib_uri),
            position=types.Position(line=1, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result = server.find_references(params)

        assert result is not None
        uris = [loc.uri for loc in result]
        # Should find in all three files
        assert lib_uri in uris
        assert consumer1_uri in uris
        assert consumer2_uri in uris

    def test_find_references_include_declaration_option(self) -> None:
        """Test that include_declaration option works correctly."""
        server = VBScriptLanguageServer()

        utils_content = '''<%
Function TestFunc()
    TestFunc = 42
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
    x = TestFunc()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        server._open_document(utils_uri, utils_content)
        server._open_document(main_uri, main_content)

        # With include_declaration=True
        params_with = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=utils_uri),
            position=types.Position(line=1, character=10),
            context=types.ReferenceContext(include_declaration=True),
        )
        result_with = server.find_references(params_with)

        # With include_declaration=False
        params_without = types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri=utils_uri),
            position=types.Position(line=1, character=10),
            context=types.ReferenceContext(include_declaration=False),
        )
        result_without = server.find_references(params_without)

        assert result_with is not None
        assert result_without is not None
        # With declaration should have more results
        assert len(result_with) >= len(result_without)


# =============================================================================
# Task 10.4: Tests for workspace change scenarios
# =============================================================================


@pytest.mark.vbscript
class TestWorkspaceChangeScenarios:
    """Tests for workspace change scenarios affecting include graph."""

    def test_file_added_updates_graph(self) -> None:
        """Test that adding a file updates the include graph."""
        server = VBScriptLanguageServer()

        # Initially just main.asp with include to non-existent file
        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        server._open_document(main_uri, main_content)

        # Include should be registered (even if target doesn't exist yet)
        includes = server._include_graph.get_direct_includes(main_uri)
        assert len(includes) == 1

        # Now add the utils.asp file
        utils_content = '''<%
Function Helper()
    Helper = 1
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        server._open_document(utils_uri, utils_content)

        # Utils should now be in the graph
        assert utils_uri in server._documents

    def test_file_removed_updates_graph(self) -> None:
        """Test that closing a file updates the include graph."""
        server = VBScriptLanguageServer()

        utils_content = '''<%
Function Helper()
    Helper = 1
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        server._open_document(utils_uri, utils_content)
        server._open_document(main_uri, main_content)

        # Both files should be in graph
        assert main_uri in server._documents
        assert utils_uri in server._documents

        # Close utils.asp
        server._close_document(utils_uri)

        # Utils should be removed
        assert utils_uri not in server._documents

        # Main still has include directive
        includes = server._include_graph.get_direct_includes(main_uri)
        assert len(includes) == 1

    def test_include_directive_changed(self) -> None:
        """Test that changing include directive updates the graph."""
        server = VBScriptLanguageServer()

        old_lib_content = '''<%
Function OldFunc()
    OldFunc = 1
End Function
%>'''
        old_lib_uri = "file:///project/old_lib.asp"

        new_lib_content = '''<%
Function NewFunc()
    NewFunc = 2
End Function
%>'''
        new_lib_uri = "file:///project/new_lib.asp"

        # Initial main includes old_lib
        main_content_v1 = '''<!--#include file="old_lib.asp"-->
<%
Sub Main()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        server._open_document(old_lib_uri, old_lib_content)
        server._open_document(new_lib_uri, new_lib_content)
        server._open_document(main_uri, main_content_v1)

        # Verify old_lib is included
        includes_v1 = server._include_graph.get_direct_includes(main_uri)
        assert any("old_lib.asp" in uri for uri in includes_v1)

        # Change include to new_lib
        main_content_v2 = '''<!--#include file="new_lib.asp"-->
<%
Sub Main()
End Sub
%>'''
        server._change_document(main_uri, main_content_v2)

        # Verify new_lib is now included
        includes_v2 = server._include_graph.get_direct_includes(main_uri)
        assert any("new_lib.asp" in uri for uri in includes_v2)
        assert not any("old_lib.asp" in uri for uri in includes_v2)

    def test_symbol_index_updated_on_file_change(self) -> None:
        """Test that symbol index is updated when included file changes."""
        server = VBScriptLanguageServer()

        # Initial utils with FuncA
        utils_v1 = '''<%
Function FuncA()
    FuncA = 1
End Function
%>'''
        utils_uri = "file:///project/utils.asp"

        main_content = '''<!--#include file="utils.asp"-->
<%
Sub Main()
End Sub
%>'''
        main_uri = "file:///project/main.asp"

        server._open_document(utils_uri, utils_v1)
        server._open_document(main_uri, main_content)

        # FuncA should be findable
        assert server._index.find_definition("FuncA") is not None
        assert server._index.find_definition("FuncB") is None

        # Change utils to have FuncB instead
        utils_v2 = '''<%
Function FuncB()
    FuncB = 2
End Function
%>'''
        server._change_document(utils_uri, utils_v2)

        # Now FuncB should be findable, FuncA should not
        assert server._index.find_definition("FuncA") is None
        assert server._index.find_definition("FuncB") is not None
