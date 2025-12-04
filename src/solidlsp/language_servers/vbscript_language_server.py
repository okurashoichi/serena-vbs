"""
Provides VBScript specific instantiation of the LanguageServer class using pygls-based VBScript LSP.
Contains various configurations and settings specific to VBScript/ASP scripting.
"""

import logging
import os
import pathlib
import sys
import threading

from solidlsp.language_servers.common import RuntimeDependency, RuntimeDependencyCollection
from solidlsp.ls import DocumentSymbols, LSPFileBuffer, SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings

log = logging.getLogger(__name__)


class VBScriptLanguageServer(SolidLanguageServer):
    """
    Provides VBScript specific instantiation of the LanguageServer class using pygls-based VBScript LSP.
    Contains various configurations and settings specific to VBScript/ASP scripting.
    """

    # Directories to ignore for VBScript projects
    IGNORED_DIRS = {"bin", "obj", "Backup", "backup", ".git", "__pycache__", "node_modules"}

    def __init__(self, config: LanguageServerConfig, repository_root_path: str, solidlsp_settings: SolidLSPSettings):
        """
        Creates a VBScriptLanguageServer instance. This class is not meant to be instantiated directly.
        Use LanguageServer.create() instead.
        """
        vbscript_lsp_cmd = self._setup_runtime_dependencies(config, solidlsp_settings)
        super().__init__(
            config,
            repository_root_path,
            ProcessLaunchInfo(cmd=vbscript_lsp_cmd, cwd=repository_root_path),
            "vbscript",
            solidlsp_settings,
        )
        self.server_ready = threading.Event()

    def is_ignored_dirname(self, dirname: str) -> bool:
        """
        Check if a directory should be ignored.
        VBScript projects commonly have bin, obj, Backup directories that should be skipped.
        """
        if super().is_ignored_dirname(dirname):
            return True
        return dirname in self.IGNORED_DIRS

    @classmethod
    def _setup_runtime_dependencies(cls, config: LanguageServerConfig, solidlsp_settings: SolidLSPSettings) -> str:
        """
        Setup runtime dependencies for VBScript Language Server and return the command to start the server.

        The VBScript LSP is implemented in Python using pygls, so we need to ensure
        pygls and lsprotocol are installed.
        """
        # Check if Python is available
        python_executable = sys.executable
        if not python_executable:
            raise RuntimeError("Python executable not found. Please ensure Python is installed and in PATH.")

        # Verify pygls and lsprotocol are available
        try:
            import lsprotocol  # noqa: F401
            import pygls  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                f"Required dependencies not found: {e}. "
                "Please install pygls and lsprotocol:\n"
                "  pip install pygls lsprotocol\n"
                "Or with uv:\n"
                "  uv pip install pygls lsprotocol"
            ) from e

        # Return command to run the VBScript LSP server module
        return f"{python_executable} -m solidlsp.language_servers.vbscript_lsp"

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize params for the VBScript Language Server.
        """
        root_uri = pathlib.Path(repository_absolute_path).as_uri()
        initialize_params = {
            "locale": "en",
            "capabilities": {
                "textDocument": {
                    "synchronization": {"didSave": True, "dynamicRegistration": True},
                    "completion": {"dynamicRegistration": True, "completionItem": {"snippetSupport": True}},
                    "definition": {"dynamicRegistration": True},
                    "references": {"dynamicRegistration": True},
                    "documentSymbol": {
                        "dynamicRegistration": True,
                        "hierarchicalDocumentSymbolSupport": True,
                        "symbolKind": {"valueSet": list(range(1, 27))},
                    },
                    "hover": {"dynamicRegistration": True, "contentFormat": ["markdown", "plaintext"]},
                },
                "workspace": {
                    "workspaceFolders": True,
                    "didChangeConfiguration": {"dynamicRegistration": True},
                    "symbol": {"dynamicRegistration": True},
                },
            },
            "processId": os.getpid(),
            "rootPath": repository_absolute_path,
            "rootUri": root_uri,
            "workspaceFolders": [
                {
                    "uri": root_uri,
                    "name": os.path.basename(repository_absolute_path),
                }
            ],
        }
        return initialize_params  # type: ignore

    def _start_server(self) -> None:
        """
        Starts the VBScript Language Server, waits for the server to be ready and yields the LanguageServer instance.
        """

        def do_nothing(params: dict) -> None:
            return

        def window_log_message(msg: dict) -> None:
            log.info(f"LSP: window/logMessage: {msg}")
            # Mark server as ready when we receive log messages
            message_text = msg.get("message", "")
            if message_text:
                log.debug(f"VBScript server message: {message_text}")
                self.server_ready.set()
                self.completions_available.set()

        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)

        log.info("Starting VBScript server process")
        self.server.start()
        initialize_params = self._get_initialize_params(self.repository_root_path)

        log.info("Sending initialize request from LSP client to LSP server and awaiting response")
        init_response = self.server.send.initialize(initialize_params)
        log.debug(f"Received initialize response from VBScript server: {init_response}")

        # Verify capabilities
        text_doc_sync = init_response["capabilities"]["textDocumentSync"]
        # textDocumentSync can be an integer or a dict with "change" key
        if isinstance(text_doc_sync, dict):
            sync_kind = text_doc_sync.get("change", 0)
        else:
            sync_kind = text_doc_sync
        assert sync_kind in [1, 2]  # Full or Incremental

        # Check document symbol support
        if "documentSymbolProvider" in init_response["capabilities"]:
            log.info("VBScript server supports document symbols")
        else:
            log.warning("Warning: VBScript server does not report document symbol support")

        # Check definition support
        if "definitionProvider" in init_response["capabilities"]:
            log.info("VBScript server supports go to definition")

        # Check references support
        if "referencesProvider" in init_response["capabilities"]:
            log.info("VBScript server supports find references")

        self.server.notify.initialized({})

        # Wait for server readiness with timeout
        log.info("Waiting for VBScript language server to be ready...")
        if not self.server_ready.wait(timeout=3.0):
            # Fallback: assume server is ready after timeout
            log.info("Timeout waiting for VBScript server ready signal, proceeding anyway")
            self.server_ready.set()
            self.completions_available.set()
        else:
            log.info("VBScript server initialization complete")

    def request_document_symbols(self, relative_file_path: str, file_buffer: LSPFileBuffer | None = None) -> DocumentSymbols:
        """
        Request document symbols for a VBScript/ASP file.

        This method supports:
        - .vbs files (pure VBScript)
        - .asp files (ASP with embedded VBScript)
        - .inc files (include files)
        """
        log.debug(f"Requesting document symbols via LSP for {relative_file_path}")

        # Use the standard LSP approach
        document_symbols = super().request_document_symbols(relative_file_path, file_buffer=file_buffer)

        # Log detection results for debugging
        functions = [s for s in document_symbols.iter_symbols() if s.get("kind") == 12]  # Function
        subs = [s for s in document_symbols.iter_symbols() if s.get("kind") == 6]  # Method (Sub)
        classes = [s for s in document_symbols.iter_symbols() if s.get("kind") == 5]  # Class

        log.info(
            f"LSP symbol detection for {relative_file_path}: "
            f"Found {len(functions)} functions, {len(subs)} subs, {len(classes)} classes"
        )

        return document_symbols
