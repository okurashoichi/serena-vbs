# Project Structure

## Organization Philosophy

Serena uses a **package-centric** organization with clear domain separation. The three main packages (`serena`, `solidlsp`, `interprompt`) have distinct responsibilities and minimal coupling.

## Directory Patterns

### Core Source (`/src/`)
**Location**: `src/`
**Purpose**: All production code organized by package
**Pattern**: Each package is independently importable and has a clear boundary

### Serena Agent (`/src/serena/`)
**Location**: `src/serena/`
**Purpose**: Main agent logic, tools, and MCP server
**Key files**:
- `agent.py` - Tool base class and agent orchestration
- `mcp.py` - MCP server implementation
- `cli.py` - Command-line interface
- `tools/` - Individual tool implementations (subclass `Tool`)

### Solid-LSP (`/src/solidlsp/`)
**Location**: `src/solidlsp/`
**Purpose**: Language Server Protocol wrapper and language-specific configs
**Key files**:
- `ls.py` - Core LSP client implementation
- `ls_config.py` - Language server configurations
- `language_servers/` - Per-language server configurations and static assets

### Language Server Configs (`/src/solidlsp/language_servers/`)
**Location**: `src/solidlsp/language_servers/{language}/`
**Purpose**: Language-specific configuration and dependencies
**Pattern**: Each language has its own directory with `config.py` and optional static files

### Tests (`/test/`)
**Location**: `test/`
**Purpose**: All test files, mirroring source structure
**Pattern**: Test repos for each language under `test/resources/repos/{language}/`

### Project Config (`.serena/`)
**Location**: `.serena/` (in target project)
**Purpose**: Per-project configuration, memories, and settings
**Note**: This is Serena's project memory, not to be confused with `.kiro/`

## Naming Conventions

- **Files**: snake_case for Python modules
- **Classes**: PascalCase (e.g., `SerenaAgent`, `LanguageServer`)
- **Functions**: snake_case (e.g., `find_symbol`, `get_references`)
- **Constants**: UPPER_SNAKE_CASE
- **Tools**: PascalCase class name, snake_case tool name

## Import Organization

```python
# Standard library first
import os
from pathlib import Path

# Third-party packages
from pydantic import BaseModel
from mcp import Server

# Local imports - use relative within package
from .agent import Tool
from ..solidlsp import LanguageServer
```

**Path Aliases**: None configured - use relative imports within packages

## Code Organization Principles

1. **Tool Pattern** - New tools subclass `serena.agent.Tool` and implement `apply()`
2. **Language Server Pattern** - New languages add config under `solidlsp/language_servers/{lang}/`
3. **Separation of Concerns** - LSP logic in solidlsp, business logic in serena
4. **Configuration over Code** - Language server differences handled via config, not conditional code

---
_Document patterns, not file trees. New files following patterns shouldn't require updates_
