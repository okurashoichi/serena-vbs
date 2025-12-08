"""
Unit tests for VBScript Symbol Index.

Tests the symbol index for tracking and searching symbols across documents.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.index import IndexedSymbol, SymbolIndex
from solidlsp.language_servers.vbscript_lsp.parser import (
    ParsedSymbol,
    Position,
    Range,
    SYMBOL_KIND_CLASS,
    SYMBOL_KIND_FUNCTION,
    SYMBOL_KIND_PROPERTY,
)


def make_symbol(
    name: str,
    kind: int = SYMBOL_KIND_FUNCTION,
    start_line: int = 0,
    end_line: int = 0,
    children: list[ParsedSymbol] | None = None,
) -> ParsedSymbol:
    """Helper to create a ParsedSymbol for testing."""
    return ParsedSymbol(
        name=name,
        kind=kind,
        range=Range(
            start=Position(line=start_line, character=0),
            end=Position(line=end_line, character=0),
        ),
        selection_range=Range(
            start=Position(line=start_line, character=0),
            end=Position(line=start_line, character=len(name)),
        ),
        children=children or [],
    )


@pytest.mark.vbscript
class TestSymbolIndexUpdate:
    """Test symbol index update operations."""

    def test_update_adds_symbols_to_index(self) -> None:
        """Test that update adds symbols to the index."""
        index = SymbolIndex()
        content = """
Function GetValue()
End Function

Function SetValue()
End Function
"""
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 2),
            make_symbol("SetValue", SYMBOL_KIND_FUNCTION, 4, 5),
        ]

        index.update("file:///test.vbs", content, symbols)

        # Should be able to find the symbols
        result = index.get_symbols_in_document("file:///test.vbs")
        assert len(result) == 2
        assert any(s.name == "GetValue" for s in result)
        assert any(s.name == "SetValue" for s in result)

    def test_update_replaces_existing_symbols(self) -> None:
        """Test that update replaces symbols for the same document."""
        index = SymbolIndex()

        # First update
        index.update("file:///test.vbs", "Function OldFunc()\nEnd Function", [make_symbol("OldFunc")])

        # Second update
        index.update("file:///test.vbs", "Function NewFunc()\nEnd Function", [make_symbol("NewFunc")])

        result = index.get_symbols_in_document("file:///test.vbs")
        assert len(result) == 1
        assert result[0].name == "NewFunc"

    def test_update_indexes_by_name(self) -> None:
        """Test that symbols are indexed by name for fast lookup."""
        index = SymbolIndex()
        symbols = [make_symbol("GetValue")]

        index.update("file:///test.vbs", "Function GetValue()\nEnd Function", symbols)

        # Should be able to find by name
        definition = index.find_definition("GetValue")
        assert definition is not None
        assert definition.name == "GetValue"

    def test_update_with_class_and_members(self) -> None:
        """Test that class members are indexed."""
        index = SymbolIndex()
        content = """
Class MyClass
    Function GetValue()
    End Function
    Property Get Name()
    End Property
End Class
"""
        class_symbol = make_symbol(
            "MyClass",
            SYMBOL_KIND_CLASS,
            1,
            7,
            children=[
                make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 2, 3),
                make_symbol("Name", SYMBOL_KIND_PROPERTY, 4, 5),
            ],
        )

        index.update("file:///test.vbs", content, [class_symbol])

        # Should index class and its members
        result = index.get_symbols_in_document("file:///test.vbs")
        names = [s.name for s in result]
        assert "MyClass" in names
        assert "GetValue" in names
        assert "Name" in names


@pytest.mark.vbscript
class TestSymbolIndexRemove:
    """Test symbol index removal operations."""

    def test_remove_deletes_document_symbols(self) -> None:
        """Test that remove deletes all symbols for a document."""
        index = SymbolIndex()
        content = "Function Func1()\nEnd Function\nFunction Func2()\nEnd Function"
        index.update("file:///test.vbs", content, [make_symbol("Func1"), make_symbol("Func2")])

        index.remove("file:///test.vbs")

        result = index.get_symbols_in_document("file:///test.vbs")
        assert len(result) == 0

    def test_remove_updates_name_index(self) -> None:
        """Test that remove also cleans up the name index."""
        index = SymbolIndex()
        index.update("file:///test.vbs", "Function GetValue()\nEnd Function", [make_symbol("GetValue")])

        index.remove("file:///test.vbs")

        definition = index.find_definition("GetValue")
        assert definition is None

    def test_remove_nonexistent_document(self) -> None:
        """Test that removing a nonexistent document doesn't fail."""
        index = SymbolIndex()
        # Should not raise
        index.remove("file:///nonexistent.vbs")


@pytest.mark.vbscript
class TestSymbolIndexFindDefinition:
    """Test definition search functionality."""

    def test_find_definition_returns_symbol(self) -> None:
        """Test that find_definition returns the symbol."""
        index = SymbolIndex()
        index.update(
            "file:///test.vbs",
            "Function GetValue()\nEnd Function",
            [make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 0, 1)],
        )

        result = index.find_definition("GetValue")

        assert result is not None
        assert result.name == "GetValue"
        assert result.uri == "file:///test.vbs"

    def test_find_definition_case_insensitive(self) -> None:
        """Test that find_definition is case-insensitive."""
        index = SymbolIndex()
        index.update("file:///test.vbs", "Function GetValue()\nEnd Function", [make_symbol("GetValue")])

        # Try different cases
        assert index.find_definition("getvalue") is not None
        assert index.find_definition("GETVALUE") is not None
        assert index.find_definition("getValue") is not None

    def test_find_definition_not_found(self) -> None:
        """Test that find_definition returns None for missing symbol."""
        index = SymbolIndex()
        index.update("file:///test.vbs", "Function GetValue()\nEnd Function", [make_symbol("GetValue")])

        result = index.find_definition("NonExistent")
        assert result is None

    def test_find_definition_multiple_documents(self) -> None:
        """Test finding definition across multiple documents."""
        index = SymbolIndex()
        index.update("file:///file1.vbs", "Function Func1()\nEnd Function", [make_symbol("Func1")])
        index.update("file:///file2.vbs", "Function Func2()\nEnd Function", [make_symbol("Func2")])

        assert index.find_definition("Func1") is not None
        assert index.find_definition("Func2") is not None

    def test_find_definition_returns_first_match(self) -> None:
        """Test that find_definition returns the first match when there are duplicates."""
        index = SymbolIndex()
        index.update("file:///file1.vbs", "Function Helper()\nEnd Function", [make_symbol("Helper", start_line=0)])
        index.update("file:///file2.vbs", "Function Helper()\nEnd Function", [make_symbol("Helper", start_line=0)])

        result = index.find_definition("Helper")
        # Should return one of them (first registered)
        assert result is not None
        assert result.name == "Helper"


@pytest.mark.vbscript
class TestSymbolIndexFindReferences:
    """Test reference search functionality."""

    def test_find_references_returns_locations(self) -> None:
        """Test that find_references returns Location objects."""
        index = SymbolIndex()
        content = """
Function GetValue()
    GetValue = 42
End Function
"""
        index.update(
            "file:///test.vbs",
            content,
            [make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3)],
        )

        result = index.find_references("GetValue", include_declaration=True)

        assert len(result) >= 1
        assert any(loc.uri == "file:///test.vbs" for loc in result)

    def test_find_references_case_insensitive(self) -> None:
        """Test that find_references is case-insensitive."""
        index = SymbolIndex()
        content = """
Function GetValue()
End Function

Sub Main()
    x = GETVALUE()
End Sub
"""
        index.update(
            "file:///test.vbs",
            content,
            [
                make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 2),
                make_symbol("Main", SYMBOL_KIND_FUNCTION, 4, 6),
            ],
        )

        assert len(index.find_references("getvalue", include_declaration=True)) >= 1
        assert len(index.find_references("GETVALUE", include_declaration=True)) >= 1

    def test_find_references_across_documents(self) -> None:
        """Test finding references across multiple documents."""
        index = SymbolIndex()
        content1 = """
Function Helper()
End Function
"""
        content2 = """
Sub Main()
    Helper
End Sub
"""
        index.update("file:///file1.vbs", content1, [make_symbol("Helper", start_line=1, end_line=2)])
        index.update("file:///file2.vbs", content2, [make_symbol("Main", start_line=1, end_line=3)])

        result = index.find_references("Helper", include_declaration=True)

        # Should find at least the definition in file1 and the call in file2
        assert len(result) >= 2
        uris = [loc.uri for loc in result]
        assert "file:///file1.vbs" in uris
        assert "file:///file2.vbs" in uris

    def test_find_references_include_declaration_false(self) -> None:
        """Test that include_declaration=False excludes the declaration."""
        index = SymbolIndex()
        content = """
Function GetValue()
    GetValue = 42
End Function

Sub Main()
    x = GetValue()
End Sub
"""
        index.update(
            "file:///test.vbs",
            content,
            [
                make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3),
                make_symbol("Main", SYMBOL_KIND_FUNCTION, 5, 7),
            ],
        )

        # With include_declaration=False, only actual references are returned (not definitions)
        result = index.find_references("GetValue", include_declaration=False)
        # Should have at least the call in Main (line 6: x = GetValue())
        assert len(result) >= 1

    def test_find_references_not_found(self) -> None:
        """Test that find_references returns empty list for missing symbol."""
        index = SymbolIndex()
        content = "Dim x"
        index.update("file:///test.vbs", content, [])

        result = index.find_references("NonExistent", include_declaration=True)
        assert result == []


@pytest.mark.vbscript
class TestSymbolIndexGetSymbolsInDocument:
    """Test document symbol retrieval."""

    def test_get_symbols_returns_all_symbols(self) -> None:
        """Test that get_symbols_in_document returns all symbols."""
        index = SymbolIndex()
        content = "Function Func1()\nEnd Function\nFunction Func2()\nEnd Function\nFunction Func3()\nEnd Function"
        index.update(
            "file:///test.vbs",
            content,
            [
                make_symbol("Func1"),
                make_symbol("Func2"),
                make_symbol("Func3"),
            ],
        )

        result = index.get_symbols_in_document("file:///test.vbs")

        assert len(result) == 3

    def test_get_symbols_empty_document(self) -> None:
        """Test that get_symbols_in_document returns empty list for unknown document."""
        index = SymbolIndex()

        result = index.get_symbols_in_document("file:///unknown.vbs")

        assert result == []

    def test_get_symbols_includes_nested_symbols(self) -> None:
        """Test that nested symbols (class members) are included."""
        index = SymbolIndex()
        content = """
Class MyClass
    Function Method1()
    End Function
    Function Method2()
    End Function
End Class
"""
        class_symbol = make_symbol(
            "MyClass",
            SYMBOL_KIND_CLASS,
            start_line=1,
            end_line=7,
            children=[make_symbol("Method1", start_line=2, end_line=3), make_symbol("Method2", start_line=4, end_line=5)],
        )

        index.update("file:///test.vbs", content, [class_symbol])

        result = index.get_symbols_in_document("file:///test.vbs")
        names = [s.name for s in result]
        assert "MyClass" in names
        assert "Method1" in names
        assert "Method2" in names


@pytest.mark.vbscript
class TestIndexedSymbol:
    """Test IndexedSymbol data class."""

    def test_indexed_symbol_creation(self) -> None:
        """Test IndexedSymbol can be created."""
        symbol = IndexedSymbol(
            name="GetValue",
            kind=SYMBOL_KIND_FUNCTION,
            uri="file:///test.vbs",
            start_line=5,
            start_character=0,
            end_line=10,
            end_character=0,
        )

        assert symbol.name == "GetValue"
        assert symbol.kind == SYMBOL_KIND_FUNCTION
        assert symbol.uri == "file:///test.vbs"
        assert symbol.start_line == 5

    def test_indexed_symbol_with_container(self) -> None:
        """Test IndexedSymbol with container_name."""
        symbol = IndexedSymbol(
            name="GetValue",
            kind=SYMBOL_KIND_FUNCTION,
            uri="file:///test.vbs",
            start_line=5,
            start_character=0,
            end_line=10,
            end_character=0,
            container_name="MyClass",
        )

        assert symbol.container_name == "MyClass"


@pytest.mark.vbscript
class TestSymbolIndexFindDefinitionInScope:
    """Test scoped definition search functionality."""

    def test_find_definition_in_scope_returns_symbol_from_specified_uris(self) -> None:
        """Test that find_definition_in_scope searches only in specified URIs."""
        index = SymbolIndex()
        index.update(
            "file:///file1.vbs",
            "Function Helper()\nEnd Function",
            [make_symbol("Helper", SYMBOL_KIND_FUNCTION, 0, 1)],
        )
        index.update(
            "file:///file2.vbs",
            "Function Helper()\nEnd Function",
            [make_symbol("Helper", SYMBOL_KIND_FUNCTION, 0, 1)],
        )
        index.update(
            "file:///file3.vbs",
            "Function Other()\nEnd Function",
            [make_symbol("Other", SYMBOL_KIND_FUNCTION, 0, 1)],
        )

        # Search only in file2 and file3
        result = index.find_definition_in_scope("Helper", ["file:///file2.vbs", "file:///file3.vbs"])

        assert result is not None
        assert result.name == "Helper"
        assert result.uri == "file:///file2.vbs"

    def test_find_definition_in_scope_not_found_in_scope(self) -> None:
        """Test that find_definition_in_scope returns None if not in scope."""
        index = SymbolIndex()
        index.update(
            "file:///file1.vbs",
            "Function Helper()\nEnd Function",
            [make_symbol("Helper", SYMBOL_KIND_FUNCTION, 0, 1)],
        )
        index.update(
            "file:///file2.vbs",
            "Function Other()\nEnd Function",
            [make_symbol("Other", SYMBOL_KIND_FUNCTION, 0, 1)],
        )

        # Search only in file2, which doesn't have Helper
        result = index.find_definition_in_scope("Helper", ["file:///file2.vbs"])

        assert result is None

    def test_find_definition_in_scope_case_insensitive(self) -> None:
        """Test that find_definition_in_scope is case-insensitive."""
        index = SymbolIndex()
        index.update(
            "file:///file1.vbs",
            "Function GetValue()\nEnd Function",
            [make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 0, 1)],
        )

        # Try different cases
        assert index.find_definition_in_scope("getvalue", ["file:///file1.vbs"]) is not None
        assert index.find_definition_in_scope("GETVALUE", ["file:///file1.vbs"]) is not None
        assert index.find_definition_in_scope("getValue", ["file:///file1.vbs"]) is not None

    def test_find_definition_in_scope_empty_uri_list(self) -> None:
        """Test that find_definition_in_scope returns None for empty URI list."""
        index = SymbolIndex()
        index.update(
            "file:///file1.vbs",
            "Function Helper()\nEnd Function",
            [make_symbol("Helper", SYMBOL_KIND_FUNCTION, 0, 1)],
        )

        result = index.find_definition_in_scope("Helper", [])

        assert result is None

    def test_find_definition_in_scope_returns_all_matches(self) -> None:
        """Test that find_definitions_in_scope returns all matching definitions."""
        index = SymbolIndex()
        index.update(
            "file:///file1.vbs",
            "Function Helper()\nEnd Function",
            [make_symbol("Helper", SYMBOL_KIND_FUNCTION, 0, 1)],
        )
        index.update(
            "file:///file2.vbs",
            "Function Helper()\nEnd Function",
            [make_symbol("Helper", SYMBOL_KIND_FUNCTION, 5, 6)],
        )
        index.update(
            "file:///file3.vbs",
            "Function Other()\nEnd Function",
            [make_symbol("Other", SYMBOL_KIND_FUNCTION, 0, 1)],
        )

        # Search all files
        result = index.find_definitions_in_scope(
            "Helper",
            ["file:///file1.vbs", "file:///file2.vbs", "file:///file3.vbs"]
        )

        assert len(result) == 2
        uris = [s.uri for s in result]
        assert "file:///file1.vbs" in uris
        assert "file:///file2.vbs" in uris

    def test_find_definitions_in_scope_empty_when_not_found(self) -> None:
        """Test that find_definitions_in_scope returns empty list when not found."""
        index = SymbolIndex()
        index.update(
            "file:///file1.vbs",
            "Function Other()\nEnd Function",
            [make_symbol("Other", SYMBOL_KIND_FUNCTION, 0, 1)],
        )

        result = index.find_definitions_in_scope("Helper", ["file:///file1.vbs"])

        assert result == []


@pytest.mark.vbscript
class TestSymbolIndexDocumentContent:
    """Test document content storage functionality."""

    def test_documents_content_attribute_exists(self) -> None:
        """Test that SymbolIndex has _documents_content attribute."""
        index = SymbolIndex()
        assert hasattr(index, "_documents_content")
        assert isinstance(index._documents_content, dict)

    def test_documents_content_starts_empty(self) -> None:
        """Test that _documents_content starts as an empty dict."""
        index = SymbolIndex()
        assert index._documents_content == {}

    def test_get_document_content_returns_content_for_indexed_uri(self) -> None:
        """Test that get_document_content returns content for indexed URI."""
        index = SymbolIndex()
        content = "Function GetValue()\nEnd Function"
        index.update("file:///test.vbs", content, [make_symbol("GetValue")])

        result = index.get_document_content("file:///test.vbs")

        assert result == content

    def test_get_document_content_returns_none_for_unknown_uri(self) -> None:
        """Test that get_document_content returns None for unknown URI."""
        index = SymbolIndex()

        result = index.get_document_content("file:///unknown.vbs")

        assert result is None

    def test_get_document_content_returns_none_after_remove(self) -> None:
        """Test that get_document_content returns None after document is removed."""
        index = SymbolIndex()
        content = "Function GetValue()\nEnd Function"
        index.update("file:///test.vbs", content, [make_symbol("GetValue")])

        index.remove("file:///test.vbs")

        result = index.get_document_content("file:///test.vbs")
        assert result is None
