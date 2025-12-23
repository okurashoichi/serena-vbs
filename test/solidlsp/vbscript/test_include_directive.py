"""
Unit tests for VBScript Include Directive data model.

Tests the IncludeDirective dataclass for representing ASP include directives.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.include_directive import IncludeDirective


@pytest.mark.vbscript
class TestIncludeDirectiveCreation:
    """Test IncludeDirective data class creation."""

    def test_include_directive_file_type(self) -> None:
        """Test IncludeDirective with file type."""
        directive = IncludeDirective(
            include_type="file",
            raw_path="../includes/common.asp",
            resolved_uri="file:///project/includes/common.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=45,
            is_valid=True,
        )

        assert directive.include_type == "file"
        assert directive.raw_path == "../includes/common.asp"
        assert directive.resolved_uri == "file:///project/includes/common.asp"
        assert directive.line == 5
        assert directive.character == 0
        assert directive.end_line == 5
        assert directive.end_character == 45
        assert directive.is_valid is True
        assert directive.error_message is None  # Default value

    def test_include_directive_virtual_type(self) -> None:
        """Test IncludeDirective with virtual type."""
        directive = IncludeDirective(
            include_type="virtual",
            raw_path="/includes/header.inc",
            resolved_uri="file:///webroot/includes/header.inc",
            line=1,
            character=0,
            end_line=1,
            end_character=40,
            is_valid=True,
        )

        assert directive.include_type == "virtual"
        assert directive.raw_path == "/includes/header.inc"
        assert directive.resolved_uri == "file:///webroot/includes/header.inc"

    def test_include_directive_invalid_with_error(self) -> None:
        """Test IncludeDirective with invalid path and error message."""
        directive = IncludeDirective(
            include_type="file",
            raw_path="../missing/file.asp",
            resolved_uri=None,
            line=10,
            character=4,
            end_line=10,
            end_character=50,
            is_valid=False,
            error_message="File not found: ../missing/file.asp",
        )

        assert directive.is_valid is False
        assert directive.resolved_uri is None
        assert directive.error_message == "File not found: ../missing/file.asp"

    def test_include_directive_all_fields(self) -> None:
        """Test IncludeDirective with all fields specified."""
        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=3,
            character=2,
            end_line=3,
            end_character=35,
            is_valid=True,
            error_message=None,
        )

        assert directive.include_type == "file"
        assert directive.raw_path == "utils.asp"
        assert directive.resolved_uri == "file:///project/utils.asp"
        assert directive.line == 3
        assert directive.character == 2
        assert directive.end_line == 3
        assert directive.end_character == 35
        assert directive.is_valid is True
        assert directive.error_message is None


@pytest.mark.vbscript
class TestIncludeDirectiveImmutability:
    """Test IncludeDirective immutability (frozen dataclass)."""

    def test_include_directive_is_immutable(self) -> None:
        """Test that IncludeDirective is a frozen dataclass (immutable)."""
        directive = IncludeDirective(
            include_type="file",
            raw_path="test.asp",
            resolved_uri="file:///test.asp",
            line=1,
            character=0,
            end_line=1,
            end_character=30,
            is_valid=True,
        )

        with pytest.raises(AttributeError):
            directive.raw_path = "new_path.asp"  # type: ignore[misc]

    def test_include_directive_is_hashable(self) -> None:
        """Test that IncludeDirective can be used in sets/dicts."""
        directive = IncludeDirective(
            include_type="file",
            raw_path="test.asp",
            resolved_uri="file:///test.asp",
            line=1,
            character=0,
            end_line=1,
            end_character=30,
            is_valid=True,
        )

        # Should be hashable because frozen=True
        directive_set = {directive}
        assert directive in directive_set


@pytest.mark.vbscript
class TestIncludeDirectiveEquality:
    """Test IncludeDirective equality."""

    def test_include_directive_equality(self) -> None:
        """Test that two IncludeDirectives with same values are equal."""
        directive1 = IncludeDirective(
            include_type="file",
            raw_path="common.asp",
            resolved_uri="file:///common.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=40,
            is_valid=True,
        )
        directive2 = IncludeDirective(
            include_type="file",
            raw_path="common.asp",
            resolved_uri="file:///common.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=40,
            is_valid=True,
        )

        assert directive1 == directive2

    def test_include_directive_inequality_different_path(self) -> None:
        """Test that IncludeDirectives with different paths are not equal."""
        directive1 = IncludeDirective(
            include_type="file",
            raw_path="common.asp",
            resolved_uri="file:///common.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=40,
            is_valid=True,
        )
        directive2 = IncludeDirective(
            include_type="file",
            raw_path="other.asp",
            resolved_uri="file:///other.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=40,
            is_valid=True,
        )

        assert directive1 != directive2

    def test_include_directive_inequality_different_type(self) -> None:
        """Test that IncludeDirectives with different types are not equal."""
        directive1 = IncludeDirective(
            include_type="file",
            raw_path="/includes/common.asp",
            resolved_uri="file:///includes/common.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=40,
            is_valid=True,
        )
        directive2 = IncludeDirective(
            include_type="virtual",
            raw_path="/includes/common.asp",
            resolved_uri="file:///includes/common.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=40,
            is_valid=True,
        )

        assert directive1 != directive2


@pytest.mark.vbscript
class TestIncludeDirectiveLiteralType:
    """Test IncludeDirective include_type literal constraint."""

    def test_include_type_file_accepted(self) -> None:
        """Test that 'file' is accepted as include_type."""
        directive = IncludeDirective(
            include_type="file",
            raw_path="test.asp",
            resolved_uri=None,
            line=1,
            character=0,
            end_line=1,
            end_character=30,
            is_valid=False,
        )
        assert directive.include_type == "file"

    def test_include_type_virtual_accepted(self) -> None:
        """Test that 'virtual' is accepted as include_type."""
        directive = IncludeDirective(
            include_type="virtual",
            raw_path="/test.asp",
            resolved_uri=None,
            line=1,
            character=0,
            end_line=1,
            end_character=30,
            is_valid=False,
        )
        assert directive.include_type == "virtual"
