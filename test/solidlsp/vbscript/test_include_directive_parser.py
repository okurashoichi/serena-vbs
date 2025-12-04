"""
Unit tests for VBScript Include Directive Parser.

Tests the IncludeDirectiveParser class for extracting and parsing ASP include
directives from ASP/VBScript source files.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.include_directive import IncludeDirective
from solidlsp.language_servers.vbscript_lsp.include_directive_parser import (
    IncludeDirectiveParser,
)


@pytest.mark.vbscript
class TestIncludeDirectiveParserBasic:
    """Test basic include directive detection."""

    def test_extract_file_include_double_quotes(self) -> None:
        """Test extracting file include with double quotes."""
        content = '<!--#include file="common.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].include_type == "file"
        assert directives[0].raw_path == "common.asp"

    def test_extract_virtual_include_double_quotes(self) -> None:
        """Test extracting virtual include with double quotes."""
        content = '<!--#include virtual="/includes/header.inc"-->'
        parser = IncludeDirectiveParser(workspace_root="/var/www")

        directives = parser.extract_includes(content, "file:///var/www/page.asp")

        assert len(directives) == 1
        assert directives[0].include_type == "virtual"
        assert directives[0].raw_path == "/includes/header.inc"

    def test_extract_no_includes(self) -> None:
        """Test content with no include directives."""
        content = """<%
        Dim x
        x = 10
        %>"""
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/test.asp")

        assert len(directives) == 0

    def test_extract_multiple_includes(self) -> None:
        """Test extracting multiple include directives."""
        content = """<!--#include file="header.asp"-->
<%
Response.Write("Hello")
%>
<!--#include file="utils.asp"-->
<!--#include virtual="/footer.inc"-->"""
        parser = IncludeDirectiveParser(workspace_root="/var/www")

        directives = parser.extract_includes(content, "file:///var/www/main.asp")

        assert len(directives) == 3
        assert directives[0].raw_path == "header.asp"
        assert directives[1].raw_path == "utils.asp"
        assert directives[2].raw_path == "/footer.inc"
        assert directives[2].include_type == "virtual"


@pytest.mark.vbscript
class TestIncludeDirectiveParserCaseInsensitive:
    """Test case-insensitive matching of include directives."""

    def test_uppercase_include(self) -> None:
        """Test uppercase INCLUDE keyword."""
        content = '<!--#INCLUDE FILE="common.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].include_type == "file"

    def test_mixed_case_include(self) -> None:
        """Test mixed case Include keyword."""
        content = '<!--#Include File="common.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].include_type == "file"

    def test_uppercase_virtual(self) -> None:
        """Test uppercase VIRTUAL keyword."""
        content = '<!--#include VIRTUAL="/header.inc"-->'
        parser = IncludeDirectiveParser(workspace_root="/var/www")

        directives = parser.extract_includes(content, "file:///var/www/page.asp")

        assert len(directives) == 1
        assert directives[0].include_type == "virtual"


@pytest.mark.vbscript
class TestIncludeDirectiveParserPositions:
    """Test line and character position tracking."""

    def test_position_first_line(self) -> None:
        """Test position tracking on the first line."""
        content = '<!--#include file="header.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].line == 0
        assert directives[0].character == 0
        assert directives[0].end_line == 0
        assert directives[0].end_character == 33

    def test_position_with_offset(self) -> None:
        """Test position tracking with leading whitespace."""
        content = '    <!--#include file="header.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].line == 0
        assert directives[0].character == 4
        assert directives[0].end_character == 37

    def test_position_on_later_line(self) -> None:
        """Test position tracking on lines after the first."""
        content = """<html>
<head>
<!--#include file="header.asp"-->
</head>"""
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].line == 2
        assert directives[0].character == 0

    def test_positions_multiple_includes(self) -> None:
        """Test position tracking for multiple includes."""
        content = """<!--#include file="a.asp"-->
<!--#include file="b.asp"-->"""
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 2
        assert directives[0].line == 0
        assert directives[1].line == 1


@pytest.mark.vbscript
class TestIncludeDirectiveParserPathResolution:
    """Test path resolution for file and virtual includes."""

    def test_resolve_relative_path_same_directory(self) -> None:
        """Test resolving relative path in the same directory."""
        content = '<!--#include file="utils.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/pages/main.asp")

        assert len(directives) == 1
        assert directives[0].resolved_uri == "file:///project/pages/utils.asp"
        assert directives[0].is_valid is True

    def test_resolve_relative_path_parent_directory(self) -> None:
        """Test resolving relative path with parent directory."""
        content = '<!--#include file="../includes/header.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/pages/main.asp")

        assert len(directives) == 1
        assert directives[0].resolved_uri == "file:///project/includes/header.asp"

    def test_resolve_relative_path_subdirectory(self) -> None:
        """Test resolving relative path in subdirectory."""
        content = '<!--#include file="lib/functions.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].resolved_uri == "file:///project/lib/functions.asp"

    def test_resolve_virtual_path_with_workspace_root(self) -> None:
        """Test resolving virtual path with workspace root."""
        import os
        import tempfile

        # Use a real temporary directory and resolve symlinks (macOS /var -> /private/var)
        with tempfile.TemporaryDirectory() as tmpdir:
            real_tmpdir = os.path.realpath(tmpdir)
            content = '<!--#include virtual="/includes/common.asp"-->'
            parser = IncludeDirectiveParser(workspace_root=real_tmpdir)

            source_uri = f"file://{real_tmpdir}/pages/main.asp"
            directives = parser.extract_includes(content, source_uri)

            assert len(directives) == 1
            expected_uri = f"file://{real_tmpdir}/includes/common.asp"
            assert directives[0].resolved_uri == expected_uri
            assert directives[0].is_valid is True

    def test_resolve_virtual_path_without_workspace_root(self) -> None:
        """Test virtual path resolution fails without workspace root."""
        content = '<!--#include virtual="/includes/common.asp"-->'
        parser = IncludeDirectiveParser()  # No workspace_root

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].is_valid is False
        assert directives[0].resolved_uri is None
        assert "workspace root" in directives[0].error_message.lower()


@pytest.mark.vbscript
class TestIncludeDirectiveParserQuoteStyles:
    """Test various quote styles in include directives."""

    def test_single_quotes(self) -> None:
        """Test include with single quotes (should not match)."""
        content = "<!--#include file='header.asp'-->"
        parser = IncludeDirectiveParser()

        # Single quotes are not standard ASP syntax but some parsers allow them
        directives = parser.extract_includes(content, "file:///project/main.asp")

        # Standard ASP only supports double quotes
        assert len(directives) == 0

    def test_no_quotes(self) -> None:
        """Test include without quotes (should not match)."""
        content = "<!--#include file=header.asp-->"
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 0


@pytest.mark.vbscript
class TestIncludeDirectiveParserEdgeCases:
    """Test edge cases and malformed includes."""

    def test_whitespace_in_directive(self) -> None:
        """Test include with extra whitespace."""
        content = '<!--  #include   file="header.asp"  -->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        # Should handle extra whitespace
        assert len(directives) == 1
        assert directives[0].raw_path == "header.asp"

    def test_empty_path(self) -> None:
        """Test include with empty path."""
        content = '<!--#include file=""-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        # Empty path should be detected but marked invalid
        assert len(directives) == 1
        assert directives[0].raw_path == ""
        assert directives[0].is_valid is False

    def test_path_with_spaces(self) -> None:
        """Test include with spaces in path."""
        content = '<!--#include file="my file.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].raw_path == "my file.asp"

    def test_inc_extension(self) -> None:
        """Test include with .inc extension."""
        content = '<!--#include file="functions.inc"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 1
        assert directives[0].raw_path == "functions.inc"

    def test_backslash_path_separator(self) -> None:
        """Test include with backslash path separator (Windows style)."""
        content = '<!--#include file="includes\\header.asp"-->'
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///C:/project/main.asp")

        assert len(directives) == 1
        assert directives[0].raw_path == "includes\\header.asp"

    def test_html_comment_not_include(self) -> None:
        """Test that regular HTML comments are not detected as includes."""
        content = "<!-- This is a comment -->"
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        assert len(directives) == 0

    def test_similar_but_not_include(self) -> None:
        """Test similar patterns that are not include directives."""
        # Note: ASP/IIS does parse <!--#include --> even with extra space after <!--
        # The second pattern with space after <!-- is technically valid ASP syntax
        content = """<!--#include file="valid.asp"-->
<!--  #include file="also_valid.asp" -->
<%' #include file="in_code.asp" %>"""
        parser = IncludeDirectiveParser()

        directives = parser.extract_includes(content, "file:///project/main.asp")

        # Both HTML-style includes are valid - the regex allows whitespace after <!--
        assert len(directives) == 2
        assert directives[0].raw_path == "valid.asp"
        assert directives[1].raw_path == "also_valid.asp"
