"""
Unit tests for VBScript Reference data model.

Tests the Reference dataclass for representing symbol references.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.reference import Reference


@pytest.mark.vbscript
class TestReferenceCreation:
    """Test Reference data class creation."""

    def test_reference_creation_basic(self) -> None:
        """Test Reference can be created with required fields."""
        ref = Reference(
            name="GetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
        )

        assert ref.name == "GetValue"
        assert ref.uri == "file:///test.vbs"
        assert ref.line == 5
        assert ref.character == 10
        assert ref.end_line == 5
        assert ref.end_character == 18
        assert ref.is_definition is False  # Default value
        assert ref.container_name is None  # Default value

    def test_reference_creation_with_is_definition(self) -> None:
        """Test Reference can be created with is_definition flag."""
        ref = Reference(
            name="GetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
            is_definition=True,
        )

        assert ref.is_definition is True

    def test_reference_creation_with_container_name(self) -> None:
        """Test Reference can be created with container_name."""
        ref = Reference(
            name="GetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
            container_name="MyClass",
        )

        assert ref.container_name == "MyClass"

    def test_reference_creation_full(self) -> None:
        """Test Reference with all fields specified."""
        ref = Reference(
            name="ProcessData",
            uri="file:///module.vbs",
            line=10,
            character=4,
            end_line=10,
            end_character=15,
            is_definition=False,
            container_name="DataHandler",
        )

        assert ref.name == "ProcessData"
        assert ref.uri == "file:///module.vbs"
        assert ref.line == 10
        assert ref.character == 4
        assert ref.end_line == 10
        assert ref.end_character == 15
        assert ref.is_definition is False
        assert ref.container_name == "DataHandler"


@pytest.mark.vbscript
class TestReferenceToLocation:
    """Test Reference to LSP Location conversion."""

    def test_to_location_basic(self) -> None:
        """Test converting Reference to LSP Location."""
        ref = Reference(
            name="GetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
        )

        location = ref.to_location()

        assert location.uri == "file:///test.vbs"
        assert location.range.start.line == 5
        assert location.range.start.character == 10
        assert location.range.end.line == 5
        assert location.range.end.character == 18

    def test_to_location_multiline(self) -> None:
        """Test converting multiline Reference to LSP Location."""
        ref = Reference(
            name="LongFunction",
            uri="file:///test.vbs",
            line=10,
            character=0,
            end_line=25,
            end_character=12,
        )

        location = ref.to_location()

        assert location.range.start.line == 10
        assert location.range.start.character == 0
        assert location.range.end.line == 25
        assert location.range.end.character == 12


@pytest.mark.vbscript
class TestReferenceEquality:
    """Test Reference equality and immutability."""

    def test_reference_equality(self) -> None:
        """Test that two References with same values are equal."""
        ref1 = Reference(
            name="GetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
        )
        ref2 = Reference(
            name="GetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
        )

        assert ref1 == ref2

    def test_reference_inequality(self) -> None:
        """Test that References with different values are not equal."""
        ref1 = Reference(
            name="GetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
        )
        ref2 = Reference(
            name="SetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
        )

        assert ref1 != ref2

    def test_reference_immutable(self) -> None:
        """Test that Reference is a frozen dataclass (immutable)."""
        ref = Reference(
            name="GetValue",
            uri="file:///test.vbs",
            line=5,
            character=10,
            end_line=5,
            end_character=18,
        )

        with pytest.raises(AttributeError):
            ref.name = "NewName"  # type: ignore[misc]
