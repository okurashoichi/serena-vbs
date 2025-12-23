"""Entry point for running the VBScript LSP server as a module.

Usage:
    python -m solidlsp.language_servers.vbscript_lsp
"""

from solidlsp.language_servers.vbscript_lsp.server import main

if __name__ == "__main__":
    main()
