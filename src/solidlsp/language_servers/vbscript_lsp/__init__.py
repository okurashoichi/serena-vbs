"""VBScript Language Server Package.

This package provides a pygls-based LSP server for VBScript/ASP files.
"""

from solidlsp.language_servers.vbscript_lsp.parser import ParsedSymbol, VBScriptParser

__all__ = ["VBScriptParser", "ParsedSymbol"]
