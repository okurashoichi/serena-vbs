"""Include Directive data model for ASP Include directives.

This module provides the IncludeDirective dataclass that represents ASP include
directives (<!--#include file="..." --> and <!--#include virtual="..." -->)
in VBScript/ASP code, supporting include reference tracking in the LSP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class IncludeDirective:
    """Represents an ASP include directive.

    This immutable dataclass holds information about an ASP include directive,
    including its type (file or virtual), path, resolved URI, and position
    in the source file.

    Attributes:
        include_type: Type of include directive ("file" or "virtual")
        raw_path: The original path specified in the directive
        resolved_uri: The resolved file URI, or None if resolution failed
        line: Starting line number (0-indexed)
        character: Starting character position
        end_line: Ending line number (0-indexed)
        end_character: Ending character position
        is_valid: Whether the include directive is valid (path resolved)
        error_message: Error message if resolution failed, None otherwise
    """

    include_type: Literal["file", "virtual"]
    raw_path: str
    resolved_uri: str | None
    line: int
    character: int
    end_line: int
    end_character: int
    is_valid: bool
    error_message: str | None = None
