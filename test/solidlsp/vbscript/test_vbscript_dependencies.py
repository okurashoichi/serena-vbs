"""
Unit tests for VBScript Language Server dependencies.

Tests that verify pygls and lsprotocol are available and properly configured.
"""

import pytest


@pytest.mark.vbscript
class TestVBScriptDependencies:
    """Test VBScript LSP dependencies availability."""

    def test_pygls_is_importable(self) -> None:
        """Test that pygls can be imported."""
        import pygls

        assert pygls is not None

    def test_pygls_version(self) -> None:
        """Test that pygls version is at least 2.0.0."""
        from importlib.metadata import version

        pygls_version = version("pygls")
        major_version = int(pygls_version.split(".")[0])
        assert major_version >= 2, f"pygls version {pygls_version} is less than 2.0.0"

    def test_lsprotocol_is_importable(self) -> None:
        """Test that lsprotocol can be imported."""
        import lsprotocol

        assert lsprotocol is not None

    def test_pygls_language_server_class(self) -> None:
        """Test that LanguageServer class is available from pygls."""
        from pygls.lsp.server import LanguageServer

        assert LanguageServer is not None

    def test_lsprotocol_types(self) -> None:
        """Test that lsprotocol types are available."""
        from lsprotocol import types

        # Verify essential types are available
        assert hasattr(types, "Position")
        assert hasattr(types, "Range")
        assert hasattr(types, "Location")
        assert hasattr(types, "DocumentSymbol")
        assert hasattr(types, "SymbolKind")

    def test_vbscript_lsp_server_module_importable(self) -> None:
        """Test that the VBScript LSP server module can be imported."""
        from solidlsp.language_servers.vbscript_lsp import server

        assert server is not None
        assert hasattr(server, "VBScriptLanguageServer")
        assert hasattr(server, "main")

    def test_vbscript_lsp_parser_importable(self) -> None:
        """Test that the VBScript parser module can be imported."""
        from solidlsp.language_servers.vbscript_lsp import parser

        assert parser is not None
        assert hasattr(parser, "VBScriptParser")

    def test_vbscript_lsp_index_importable(self) -> None:
        """Test that the VBScript index module can be imported."""
        from solidlsp.language_servers.vbscript_lsp import index

        assert index is not None
        assert hasattr(index, "SymbolIndex")


@pytest.mark.vbscript
class TestVBScriptLanguageServerDependencyCheck:
    """Test VBScript Language Server dependency check functionality."""

    def test_wrapper_can_verify_dependencies(self) -> None:
        """Test that the wrapper class can verify dependencies."""
        from solidlsp.language_servers.vbscript_language_server import (
            VBScriptLanguageServer,
        )
        from solidlsp.ls_config import LanguageServerConfig, Language
        from solidlsp.settings import SolidLSPSettings

        # Create minimal config
        config = LanguageServerConfig(code_language=Language.VBSCRIPT)
        settings = SolidLSPSettings()

        # This should not raise an error if dependencies are available
        cmd = VBScriptLanguageServer._setup_runtime_dependencies(config, settings)
        assert cmd is not None
        assert "vbscript_lsp" in cmd


@pytest.mark.vbscript
class TestPyprojectTomlDependencies:
    """Test that pyproject.toml has the required dependencies."""

    def test_pyproject_has_pygls_dependency(self) -> None:
        """Test that pyproject.toml includes pygls in dependencies."""
        import tomllib
        from pathlib import Path

        # Find pyproject.toml
        project_root = Path(__file__).parent.parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        dependencies = pyproject.get("project", {}).get("dependencies", [])
        pygls_found = any("pygls" in dep for dep in dependencies)
        assert pygls_found, "pygls not found in pyproject.toml dependencies"

    def test_pyproject_has_lsprotocol_dependency(self) -> None:
        """Test that pyproject.toml includes lsprotocol in dependencies."""
        import tomllib
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        dependencies = pyproject.get("project", {}).get("dependencies", [])
        lsprotocol_found = any("lsprotocol" in dep for dep in dependencies)
        assert lsprotocol_found, "lsprotocol not found in pyproject.toml dependencies"

    def test_pyproject_has_vbscript_marker(self) -> None:
        """Test that pyproject.toml has vbscript pytest marker registered."""
        import tomllib
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        markers = pyproject.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("markers", [])
        vbscript_marker_found = any("vbscript" in marker for marker in markers)
        assert vbscript_marker_found, "vbscript marker not found in pytest markers"
