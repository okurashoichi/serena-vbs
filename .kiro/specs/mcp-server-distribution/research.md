# Research & Design Decisions

## Summary
- **Feature**: `mcp-server-distribution`
- **Discovery Scope**: Simple Addition（READMEドキュメント更新のみ）
- **Key Findings**:
  - GitHubリポジトリURL: `git+https://github.com/okurashoichi/serena-vbs`
  - `uvx` コマンドで直接実行可能（PyPI公開不要）
  - 既存の `pyproject.toml` に `serena` CLIコマンドが定義済み

## Research Log

### uvx コマンドによる配布方法
- **Context**: MCPサーバーの配布方法の調査
- **Sources Consulted**: pyproject.toml、uv公式ドキュメント
- **Findings**:
  - `uvx --from git+https://... serena start-mcp-server` で直接実行可能
  - 一時的な仮想環境を自動作成し、依存関係をインストール
  - PyPI公開なしでGitHubリポジトリから配布可能
- **Implications**: READMEに設定例を追加するだけで配布完了

### MCP設定JSONの形式
- **Context**: Claude Code/Desktop用の設定形式の調査
- **Findings**:
  - Claude Code: `~/.config/claude/claude_code_config.json` の `mcpServers` セクション
  - Claude Desktop: `claude_desktop_config.json` の同様の形式
  - 両方とも `command` + `args` 形式でコマンドを指定
- **Implications**: 統一した設定例をREADMEに記載可能

## Design Decisions

### Decision: PyPI公開を行わずGitHub URLによる配布
- **Context**: 配布方法の簡素化
- **Alternatives Considered**:
  1. PyPI公開 — 短いコマンド（`uvx serena-vbs`）、バージョン管理が容易
  2. GitHub URL配布 — 設定不要、即時反映、追加作業なし
- **Selected Approach**: GitHub URL配布
- **Rationale**:
  - PyPI公開には追加の設定・管理が必要
  - GitHub URLでも十分使いやすい
  - 最新コミットが即時反映される
- **Trade-offs**: コマンドが長くなるが、READMEからコピペすれば問題なし

## Risks & Mitigations
- リポジトリ名/URL変更時にユーザー設定が壊れる — READMEで注意喚起

## References
- [uv公式ドキュメント](https://docs.astral.sh/uv/) — uvxの仕組み
- [MCP公式ドキュメント](https://modelcontextprotocol.io/) — MCP設定形式
