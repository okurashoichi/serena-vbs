"""
Unit tests for VBScript Language Server wrapper (Serena integration).

Tests the SolidLanguageServer implementation that wraps the pygls-based VBScript LSP.
"""

import pytest

from solidlsp.ls_config import FilenameMatcher, Language


@pytest.mark.vbscript
class TestVBScriptLanguageEnum:
    """Test VBScript Language enum entry and configuration."""

    def test_vbscript_in_language_enum(self) -> None:
        """Test that VBSCRIPT is a valid Language enum member."""
        assert hasattr(Language, "VBSCRIPT")
        assert Language.VBSCRIPT.value == "vbscript"

    def test_vbscript_str_conversion(self) -> None:
        """Test that VBSCRIPT converts to string correctly."""
        assert str(Language.VBSCRIPT) == "vbscript"

    def test_vbscript_not_experimental(self) -> None:
        """Test that VBSCRIPT is not marked as experimental."""
        assert not Language.VBSCRIPT.is_experimental()

    def test_vbscript_in_iter_all(self) -> None:
        """Test that VBSCRIPT is included in iter_all."""
        all_languages = list(Language.iter_all())
        assert Language.VBSCRIPT in all_languages


@pytest.mark.vbscript
class TestVBScriptFilenameMatcher:
    """Test VBScript file extension matching."""

    def test_vbs_extension_is_relevant(self) -> None:
        """Test that .vbs files are recognized."""
        matcher = Language.VBSCRIPT.get_source_fn_matcher()
        assert matcher.is_relevant_filename("script.vbs")
        assert matcher.is_relevant_filename("path/to/script.vbs")
        assert matcher.is_relevant_filename("Script.VBS")  # case insensitivity

    def test_asp_extension_is_relevant(self) -> None:
        """Test that .asp files are recognized."""
        matcher = Language.VBSCRIPT.get_source_fn_matcher()
        assert matcher.is_relevant_filename("page.asp")
        assert matcher.is_relevant_filename("path/to/page.asp")
        assert matcher.is_relevant_filename("Page.ASP")

    def test_inc_extension_is_relevant(self) -> None:
        """Test that .inc files are recognized."""
        matcher = Language.VBSCRIPT.get_source_fn_matcher()
        assert matcher.is_relevant_filename("include.inc")
        assert matcher.is_relevant_filename("path/to/include.inc")
        assert matcher.is_relevant_filename("Include.INC")

    def test_other_extensions_not_relevant(self) -> None:
        """Test that other file extensions are not recognized."""
        matcher = Language.VBSCRIPT.get_source_fn_matcher()
        assert not matcher.is_relevant_filename("script.py")
        assert not matcher.is_relevant_filename("script.js")
        assert not matcher.is_relevant_filename("script.vb")  # VB.NET, not VBScript
        assert not matcher.is_relevant_filename("script.txt")


@pytest.mark.vbscript
class TestVBScriptLanguageServerClass:
    """Test VBScript language server class retrieval."""

    def test_get_ls_class_returns_vbscript_server(self) -> None:
        """Test that get_ls_class returns VBScriptLanguageServer."""
        from solidlsp.language_servers.vbscript_language_server import (
            VBScriptLanguageServer,
        )

        ls_class = Language.VBSCRIPT.get_ls_class()
        assert ls_class is VBScriptLanguageServer

    def test_from_ls_class_returns_vbscript(self) -> None:
        """Test that from_ls_class returns VBSCRIPT for VBScriptLanguageServer."""
        from solidlsp.language_servers.vbscript_language_server import (
            VBScriptLanguageServer,
        )

        lang = Language.from_ls_class(VBScriptLanguageServer)
        assert lang is Language.VBSCRIPT
