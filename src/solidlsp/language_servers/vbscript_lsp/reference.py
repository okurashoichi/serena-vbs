"""Reference data model for VBScript Symbol References.

This module provides the Reference dataclass that represents symbol references
in VBScript code, supporting find references functionality in the LSP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lsprotocol import types


@dataclass(frozen=True)
class Reference:
    """Represents a symbol reference in VBScript code.

    This immutable dataclass holds the position and metadata of a symbol reference,
    supporting the LSP textDocument/references functionality.

    Attributes:
        name: The symbol name being referenced
        uri: Document URI where the reference is located
        line: Starting line number (0-indexed)
        character: Starting character position
        end_line: Ending line number (0-indexed)
        end_character: Ending character position
        is_definition: Whether this is a symbol definition (not a reference)
        container_name: Name of the containing symbol (e.g., function or class)
    """

    name: str
    uri: str
    line: int
    character: int
    end_line: int
    end_character: int
    is_definition: bool = False
    container_name: str | None = None

    def to_location(self) -> types.Location:
        """Convert this reference to an LSP Location object.

        Returns:
            An LSP Location object representing this reference's position.
        """
        from lsprotocol import types

        return types.Location(
            uri=self.uri,
            range=types.Range(
                start=types.Position(line=self.line, character=self.character),
                end=types.Position(line=self.end_line, character=self.end_character),
            ),
        )
