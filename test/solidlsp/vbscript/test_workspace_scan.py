"""
Unit tests for VBScript LSP workspace scanning functionality.

Tests the workspace scanning helpers for file extension and directory filtering.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.server import VBScriptLanguageServer


@pytest.mark.vbscript
class TestIsTargetFile:
    """Test target file extension detection."""

    def test_vbs_lowercase_is_target(self) -> None:
        """Test that .vbs files are recognized as targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("script.vbs") is True

    def test_vbs_uppercase_is_target(self) -> None:
        """Test that .VBS files are recognized as targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("script.VBS") is True

    def test_asp_lowercase_is_target(self) -> None:
        """Test that .asp files are recognized as targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("page.asp") is True

    def test_asp_uppercase_is_target(self) -> None:
        """Test that .ASP files are recognized as targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("page.ASP") is True

    def test_inc_lowercase_is_target(self) -> None:
        """Test that .inc files are recognized as targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("include.inc") is True

    def test_inc_uppercase_is_target(self) -> None:
        """Test that .INC files are recognized as targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("include.INC") is True

    def test_txt_is_not_target(self) -> None:
        """Test that .txt files are not targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("readme.txt") is False

    def test_js_is_not_target(self) -> None:
        """Test that .js files are not targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("script.js") is False

    def test_py_is_not_target(self) -> None:
        """Test that .py files are not targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("test.py") is False

    def test_no_extension_is_not_target(self) -> None:
        """Test that files without extension are not targets."""
        server = VBScriptLanguageServer()
        assert server._is_target_file("Makefile") is False


@pytest.mark.vbscript
class TestShouldSkipDirectory:
    """Test directory exclusion logic."""

    def test_git_directory_is_skipped(self) -> None:
        """Test that .git directory is skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory(".git") is True

    def test_node_modules_is_skipped(self) -> None:
        """Test that node_modules directory is skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory("node_modules") is True

    def test_backup_is_skipped(self) -> None:
        """Test that Backup directory is skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory("Backup") is True

    def test_bin_is_skipped(self) -> None:
        """Test that bin directory is skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory("bin") is True

    def test_obj_is_skipped(self) -> None:
        """Test that obj directory is skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory("obj") is True

    def test_hidden_directory_is_skipped(self) -> None:
        """Test that hidden directories (starting with .) are skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory(".vscode") is True
        assert server._should_skip_directory(".idea") is True
        assert server._should_skip_directory(".cache") is True

    def test_src_directory_is_not_skipped(self) -> None:
        """Test that src directory is not skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory("src") is False

    def test_lib_directory_is_not_skipped(self) -> None:
        """Test that lib directory is not skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory("lib") is False

    def test_includes_directory_is_not_skipped(self) -> None:
        """Test that includes directory is not skipped."""
        server = VBScriptLanguageServer()
        assert server._should_skip_directory("includes") is False


@pytest.mark.vbscript
class TestReadFileContent:
    """Test file content reading functionality."""

    def test_read_utf8_file(self, tmp_path) -> None:
        """Test reading a UTF-8 encoded file."""
        test_file = tmp_path / "test.vbs"
        test_file.write_text("Function Test()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer()
        content = server._read_file_content(str(test_file))

        assert content is not None
        assert "Function Test()" in content

    def test_read_nonexistent_file_returns_none(self) -> None:
        """Test reading a nonexistent file returns None."""
        server = VBScriptLanguageServer()
        content = server._read_file_content("/nonexistent/path/file.vbs")

        assert content is None

    def test_read_file_with_encoding_error_uses_replace(self, tmp_path) -> None:
        """Test reading a file with encoding errors uses replace mode."""
        test_file = tmp_path / "test.vbs"
        # Write bytes that are invalid UTF-8
        test_file.write_bytes(b"Function Test()\n\x80\x81\x82\nEnd Function")

        server = VBScriptLanguageServer()
        content = server._read_file_content(str(test_file))

        # Should still return content with replacement characters
        assert content is not None
        assert "Function Test()" in content
        assert "End Function" in content

    def test_read_empty_file(self, tmp_path) -> None:
        """Test reading an empty file."""
        test_file = tmp_path / "empty.vbs"
        test_file.write_text("", encoding="utf-8")

        server = VBScriptLanguageServer()
        content = server._read_file_content(str(test_file))

        assert content == ""

    def test_read_file_with_japanese_content(self, tmp_path) -> None:
        """Test reading a file with Japanese content."""
        test_file = tmp_path / "japanese.vbs"
        test_file.write_text("' コメント\nFunction テスト()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer()
        content = server._read_file_content(str(test_file))

        assert content is not None
        assert "コメント" in content
        assert "テスト" in content


@pytest.mark.vbscript
class TestScanWorkspace:
    """Test workspace scanning functionality."""

    def test_scan_empty_directory(self, tmp_path) -> None:
        """Test scanning an empty directory returns 0."""
        server = VBScriptLanguageServer(workspace_root=str(tmp_path))
        count = server._scan_workspace(str(tmp_path))

        assert count == 0

    def test_scan_single_vbs_file(self, tmp_path) -> None:
        """Test scanning a directory with a single .vbs file."""
        test_file = tmp_path / "test.vbs"
        test_file.write_text("Function Test()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))
        count = server._scan_workspace(str(tmp_path))

        assert count == 1

    def test_scan_multiple_files(self, tmp_path) -> None:
        """Test scanning multiple VBScript-related files."""
        (tmp_path / "test.vbs").write_text("Function VBS()\nEnd Function", encoding="utf-8")
        (tmp_path / "page.asp").write_text("<%\nFunction ASP()\nEnd Function\n%>", encoding="utf-8")
        (tmp_path / "include.inc").write_text("Function INC()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))
        count = server._scan_workspace(str(tmp_path))

        assert count == 3

    def test_scan_ignores_non_target_files(self, tmp_path) -> None:
        """Test that non-VBScript files are ignored."""
        (tmp_path / "test.vbs").write_text("Function VBS()\nEnd Function", encoding="utf-8")
        (tmp_path / "readme.txt").write_text("This is a readme", encoding="utf-8")
        (tmp_path / "script.js").write_text("function js() {}", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))
        count = server._scan_workspace(str(tmp_path))

        assert count == 1

    def test_scan_nested_directories(self, tmp_path) -> None:
        """Test scanning files in nested directories."""
        (tmp_path / "root.vbs").write_text("Function Root()\nEnd Function", encoding="utf-8")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.vbs").write_text("Function Nested()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))
        count = server._scan_workspace(str(tmp_path))

        assert count == 2

    def test_scan_skips_excluded_directories(self, tmp_path) -> None:
        """Test that excluded directories are skipped."""
        (tmp_path / "main.vbs").write_text("Function Main()\nEnd Function", encoding="utf-8")

        # Create excluded directories with files
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "hooks.vbs").write_text("Function Git()\nEnd Function", encoding="utf-8")

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "lib.vbs").write_text("Function Node()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))
        count = server._scan_workspace(str(tmp_path))

        # Only main.vbs should be counted
        assert count == 1

    def test_scan_indexes_symbols(self, tmp_path) -> None:
        """Test that scanned files have their symbols indexed."""
        test_file = tmp_path / "test.vbs"
        test_file.write_text("Function TestFunc()\nEnd Function\n\nSub TestSub()\nEnd Sub", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))
        server._scan_workspace(str(tmp_path))

        # Verify symbols are in the index
        definition = server._index.find_definition("TestFunc")
        assert definition is not None

        definition = server._index.find_definition("TestSub")
        assert definition is not None

    def test_scan_nonexistent_directory_returns_zero(self) -> None:
        """Test scanning a nonexistent directory returns 0."""
        server = VBScriptLanguageServer()
        count = server._scan_workspace("/nonexistent/path")

        assert count == 0


@pytest.mark.vbscript
class TestAnalysisComplete:
    """Test analysis completion notification."""

    def test_analysis_complete_exists(self) -> None:
        """Test that analysis_complete event attribute exists."""
        server = VBScriptLanguageServer()
        assert hasattr(server, "analysis_complete")
        assert hasattr(server.analysis_complete, "is_set")
        assert hasattr(server.analysis_complete, "set")
        assert hasattr(server.analysis_complete, "wait")

    def test_analysis_complete_set_after_init(self, tmp_path) -> None:
        """Test that analysis_complete is set after server initialization."""
        (tmp_path / "test.vbs").write_text("Function Test()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))

        # analysis_complete should be set after init
        assert server.analysis_complete.is_set()


@pytest.mark.vbscript
class TestServerInitialization:
    """Test server initialization with workspace scanning."""

    def test_workspace_scanned_on_init(self, tmp_path) -> None:
        """Test that workspace is scanned during server initialization."""
        (tmp_path / "test.vbs").write_text("Function Test()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))

        # Verify file was scanned and indexed
        definition = server._index.find_definition("Test")
        assert definition is not None

    def test_analysis_complete_set_on_init(self, tmp_path) -> None:
        """Test that analysis_complete is set after server initialization."""
        (tmp_path / "test.vbs").write_text("Function Test()\nEnd Function", encoding="utf-8")

        server = VBScriptLanguageServer(workspace_root=str(tmp_path))

        assert server.analysis_complete.is_set()

    def test_no_scan_without_workspace_root(self) -> None:
        """Test that no scan occurs when workspace_root is None.

        When workspace_root is None at construction, analysis_complete is NOT set
        because the scan happens during the LSP initialize handler in production.
        """
        server = VBScriptLanguageServer(workspace_root=None)

        # analysis_complete should NOT be set yet (waiting for LSP initialize)
        assert not server.analysis_complete.is_set()
