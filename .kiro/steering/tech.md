# Technology Stack

## Architecture

Serena follows a modular architecture with clear separation:
- **Solid-LSP** (`src/solidlsp`) - Core LSP wrapper providing synchronous language server communication
- **Serena Agent** (`src/serena`) - Tool implementations and MCP server
- **Interprompt** (`src/interprompt`) - Prompt management utilities

## Core Technologies

- **Language**: Python 3.11 (strict version requirement)
- **Package Manager**: uv (for dependency management and virtual environments)
- **Protocol**: MCP (Model Context Protocol) for LLM integration
- **Foundation**: Language Server Protocol (LSP) for code intelligence

## Key Libraries

| Library | Purpose |
|---------|---------|
| `mcp` | MCP SDK for exposing tools to LLM clients |
| `pyright` | Python language server (bundled) |
| `pydantic` | Data validation and settings management |
| `Flask` | Dashboard and log viewer GUI |
| `anthropic` | Claude API integration for task execution |

## Development Standards

### Type Safety
- Strict mypy configuration enabled
- `disallow_untyped_defs = true` - All functions must be typed
- `strict_equality = true` - Strict type comparisons

### Code Quality
- **Formatter**: Black (line-length: 140)
- **Linter**: Ruff with comprehensive rule set
- No explicit docstring requirements (D100-D107 ignored)

### Testing
- **Framework**: pytest with xdist for parallel execution
- **Snapshots**: syrupy for snapshot testing of symbolic operations
- Language-specific markers for conditional test execution

## Development Environment

### Required Tools
- Python 3.11 (exact version, not 3.12+)
- uv (package manager)
- Language servers for target languages

### Common Commands
```bash
# Dev: Run tests
poe test

# Lint: Check formatting and linting
poe lint

# Format: Auto-fix formatting
poe format

# Type check
poe type-check

# Documentation build
poe doc-build
```

## Key Technical Decisions

1. **Synchronous LSP** - Solid-LSP wraps async LSP calls synchronously for simpler tool implementation
2. **Symbol-centric API** - All code operations reference symbols, not file paths and line numbers
3. **Per-project Configuration** - Each project can specify language servers and settings via `.serena/`
4. **MCP-first** - Primary integration method is MCP server, with fallback to direct API

---
_Document standards and patterns, not every dependency_
