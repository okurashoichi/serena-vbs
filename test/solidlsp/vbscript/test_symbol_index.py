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
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 0, 5),
            make_symbol("SetValue", SYMBOL_KIND_FUNCTION, 7, 12),
        ]

        index.update("file:///test.vbs", symbols)

        # Should be able to find the symbols
        result = index.get_symbols_in_document("file:///test.vbs")
        assert len(result) == 2
        assert any(s.name == "GetValue" for s in result)
        assert any(s.name == "SetValue" for s in result)

    def test_update_replaces_existing_symbols(self) -> None:
        """Test that update replaces symbols for the same document."""
        index = SymbolIndex()

        # First update
        index.update("file:///test.vbs", [make_symbol("OldFunc")])

        # Second update
        index.update("file:///test.vbs", [make_symbol("NewFunc")])

        result = index.get_symbols_in_document("file:///test.vbs")
        assert len(result) == 1
        assert result[0].name == "NewFunc"

    def test_update_indexes_by_name(self) -> None:
        """Test that symbols are indexed by name for fast lookup."""
        index = SymbolIndex()
        symbols = [make_symbol("GetValue")]

        index.update("file:///test.vbs", symbols)

        # Should be able to find by name
        definition = index.find_definition("GetValue")
        assert definition is not None
        assert definition.name == "GetValue"

    def test_update_with_class_and_members(self) -> None:
        """Test that class members are indexed."""
        index = SymbolIndex()
        class_symbol = make_symbol(
            "MyClass",
            SYMBOL_KIND_CLASS,
            0,
            20,
            children=[
                make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 5, 10),
                make_symbol("Name", SYMBOL_KIND_PROPERTY, 12, 18),
            ],
        )

        index.update("file:///test.vbs", [class_symbol])

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
        index.update("file:///test.vbs", [make_symbol("Func1"), make_symbol("Func2")])

        index.remove("file:///test.vbs")

        result = index.get_symbols_in_document("file:///test.vbs")
        assert len(result) == 0

    def test_remove_updates_name_index(self) -> None:
        """Test that remove also cleans up the name index."""
        index = SymbolIndex()
        index.update("file:///test.vbs", [make_symbol("GetValue")])

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
            [make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 5, 10)],
        )

        result = index.find_definition("GetValue")

        assert result is not None
        assert result.name == "GetValue"
        assert result.uri == "file:///test.vbs"

    def test_find_definition_case_insensitive(self) -> None:
        """Test that find_definition is case-insensitive."""
        index = SymbolIndex()
        index.update("file:///test.vbs", [make_symbol("GetValue")])

        # Try different cases
        assert index.find_definition("getvalue") is not None
        assert index.find_definition("GETVALUE") is not None
        assert index.find_definition("getValue") is not None

    def test_find_definition_not_found(self) -> None:
        """Test that find_definition returns None for missing symbol."""
        index = SymbolIndex()
        index.update("file:///test.vbs", [make_symbol("GetValue")])

        result = index.find_definition("NonExistent")
        assert result is None

    def test_find_definition_multiple_documents(self) -> None:
        """Test finding definition across multiple documents."""
        index = SymbolIndex()
        index.update("file:///file1.vbs", [make_symbol("Func1")])
        index.update("file:///file2.vbs", [make_symbol("Func2")])

        assert index.find_definition("Func1") is not None
        assert index.find_definition("Func2") is not None

    def test_find_definition_returns_first_match(self) -> None:
        """Test that find_definition returns the first match when there are duplicates."""
        index = SymbolIndex()
        index.update("file:///file1.vbs", [make_symbol("Helper", start_line=0)])
        index.update("file:///file2.vbs", [make_symbol("Helper", start_line=10)])

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
        index.update(
            "file:///test.vbs",
            [make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 5, 10)],
        )

        result = index.find_references("GetValue", include_declaration=True)

        assert len(result) == 1
        assert result[0].uri == "file:///test.vbs"

    def test_find_references_case_insensitive(self) -> None:
        """Test that find_references is case-insensitive."""
        index = SymbolIndex()
        index.update("file:///test.vbs", [make_symbol("GetValue")])

        assert len(index.find_references("getvalue", include_declaration=True)) == 1
        assert len(index.find_references("GETVALUE", include_declaration=True)) == 1

    def test_find_references_across_documents(self) -> None:
        """Test finding references across multiple documents."""
        index = SymbolIndex()
        # Same function name in different files
        index.update("file:///file1.vbs", [make_symbol("Helper")])
        index.update("file:///file2.vbs", [make_symbol("Helper")])

        result = index.find_references("Helper", include_declaration=True)

        assert len(result) == 2
        uris = [loc.uri for loc in result]
        assert "file:///file1.vbs" in uris
        assert "file:///file2.vbs" in uris

    def test_find_references_include_declaration_false(self) -> None:
        """Test that include_declaration=False excludes the declaration.

        Note: In a real implementation, this would require tracking
        actual references vs declarations. For now, the index only
        tracks declarations, so this returns an empty list.
        """
        index = SymbolIndex()
        index.update("file:///test.vbs", [make_symbol("GetValue")])

        # With include_declaration=False, only actual references are returned
        # Since we only track declarations, this should be empty
        result = index.find_references("GetValue", include_declaration=False)
        assert len(result) == 0

    def test_find_references_not_found(self) -> None:
        """Test that find_references returns empty list for missing symbol."""
        index = SymbolIndex()

        result = index.find_references("NonExistent", include_declaration=True)
        assert result == []


@pytest.mark.vbscript
class TestSymbolIndexGetSymbolsInDocument:
    """Test document symbol retrieval."""

    def test_get_symbols_returns_all_symbols(self) -> None:
        """Test that get_symbols_in_document returns all symbols."""
        index = SymbolIndex()
        index.update(
            "file:///test.vbs",
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
        class_symbol = make_symbol(
            "MyClass",
            SYMBOL_KIND_CLASS,
            children=[make_symbol("Method1"), make_symbol("Method2")],
        )

        index.update("file:///test.vbs", [class_symbol])

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
