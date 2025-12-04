# Research & Design Decisions

## Summary
- **Feature**: `find-referencing-symbols`
- **Discovery Scope**: Extension（既存システムへの機能追加）
- **Key Findings**:
  - Serenaには`FindReferencingSymbolsTool`が既に存在し、MCPツールとして公開されている
  - VBScript LSPサーバーは`textDocument/references`リクエストをサポートしているが、現在は宣言のみを追跡
  - 実際の参照検索（関数呼び出し、変数使用箇所）にはパーサーの拡張が必要

## Research Log

### VBScript Language Server 現状分析

- **Context**: VBScript LSPサーバーの参照検索機能の現状を調査
- **Sources Consulted**:
  - `src/solidlsp/language_servers/vbscript_lsp/server.py`
  - `src/solidlsp/language_servers/vbscript_lsp/index.py`
  - `src/solidlsp/language_servers/vbscript_lsp/parser.py`
- **Findings**:
  - `VBScriptLanguageServer`は`referencesProvider: true`を初期化パラメータで宣言 (`vbscript_language_server.py:97`)
  - `SymbolIndex.find_references()`は現在宣言のみを返す（`index.py:129-172`のコメント参照）
  - パーサーはシンボル定義のみを抽出し、参照（呼び出し箇所）は追跡していない
- **Implications**:
  - 真の参照検索を実現するには、パーサーを拡張してシンボル参照を追跡する必要がある
  - 代替案として、ファイル内テキスト検索ベースの参照検索も可能

### 既存Serenaツール構造分析

- **Context**: 既存の`find_referencing_symbols`実装パターンを調査
- **Sources Consulted**:
  - `src/serena/tools/symbol_tools.py:151-201` (FindReferencingSymbolsTool)
  - `src/serena/symbol.py:526-605` (LanguageServerSymbolRetriever.find_referencing_symbols)
  - `src/solidlsp/ls.py:1361-1449` (SolidLanguageServer.request_referencing_symbols)
- **Findings**:
  - `FindReferencingSymbolsTool`はMCPツールとして既に存在
  - 内部で`LanguageServerSymbolRetriever.find_referencing_symbols`を呼び出す
  - 最終的に`SolidLanguageServer.request_referencing_symbols`を使用
  - `request_referencing_symbols`は`request_references`（LSP `textDocument/references`）を呼び出し、各参照の含有シンボルを特定
- **Implications**:
  - 既存のツールとインフラは完全に機能している
  - 問題はVBScript LSPサーバー側の`find_references`実装が不完全なこと

### VBScript参照追跡の実装アプローチ

- **Context**: VBScriptの参照検索を実装するための技術的アプローチを検討
- **Sources Consulted**:
  - VBScript言語仕様
  - 既存のパーサー実装 (`vbscript_lsp/parser.py`)
- **Findings**:
  - **アプローチ1: パーサー拡張** - ASTレベルで識別子参照を追跡
    - 長所: 正確な参照検出、文脈を考慮した検索
    - 短所: パーサーの大幅な変更が必要、実装コスト高
  - **アプローチ2: テキストベース検索** - ファイル内でシンボル名をgrep
    - 長所: 実装が簡単、すぐに機能
    - 短所: 誤検出の可能性（コメント内、文字列内のマッチ）
  - **アプローチ3: 正規表現ベース検索** - VBScript構文を考慮した正規表現マッチング
    - 長所: テキスト検索より精度が高い、実装コスト中程度
    - 短所: 複雑な構文パターンに対応しきれない可能性
- **Implications**:
  - MVP段階ではアプローチ3（正規表現ベース）が現実的
  - 将来的にはアプローチ1に移行して精度向上

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| パーサー拡張 | VBScriptパーサーを拡張して参照を追跡 | 正確、文脈考慮 | 大幅な実装コスト | 将来的な理想形 |
| テキスト検索 | ファイル内テキストマッチング | 簡単実装 | 誤検出多い | 最小限の実装 |
| 正規表現検索 | VBScript構文を考慮した正規表現 | バランス良好 | 複雑構文に弱い | 推奨アプローチ |

## Design Decisions

### Decision: 正規表現ベースの参照検索実装

- **Context**: VBScript LSPサーバーに参照検索機能を追加する必要がある
- **Alternatives Considered**:
  1. パーサー拡張 — ASTレベルで識別子参照を追跡
  2. テキスト検索 — 単純な文字列マッチング
  3. 正規表現検索 — VBScript構文を考慮した正規表現パターン
- **Selected Approach**: 正規表現ベースの参照検索
  - `SymbolIndex`に参照追跡機能を追加
  - 各ファイルを解析時に識別子使用箇所も記録
  - VBScript構文を考慮したパターンでコメント・文字列内を除外
- **Rationale**: 実装コストと精度のバランスが最も良い。パーサーの大規模変更なしに合理的な精度を達成可能
- **Trade-offs**:
  - 長所: 既存インフラを活用、実装期間短縮
  - 短所: 完全な精度ではない（エッジケースで誤検出の可能性）
- **Follow-up**: 精度に問題があれば、将来的にパーサー拡張に移行

### Decision: 既存ツール構造の維持

- **Context**: MCPツールとしての公開方法を決定
- **Alternatives Considered**:
  1. 新規ツールクラス作成
  2. 既存`FindReferencingSymbolsTool`の使用
- **Selected Approach**: 既存`FindReferencingSymbolsTool`をそのまま使用
  - VBScript LSPサーバー側の`find_references`実装を改善するだけ
  - Serena側のツールコードは変更不要
- **Rationale**: 既存のツール構造が完全に機能しており、問題はLSPサーバー側にある
- **Trade-offs**:
  - 長所: 変更範囲最小化、既存テストの再利用可能
  - 短所: なし

## Risks & Mitigations

- **VBScript構文の複雑さ** — 正規表現でカバーしきれないエッジケースが存在する可能性
  - Mitigation: 主要な構文パターンを網羅し、段階的に改善
- **パフォーマンス** — 大規模プロジェクトでの参照検索が遅くなる可能性
  - Mitigation: シンボルインデックスのキャッシュを活用
- **誤検出** — コメント内や文字列内のマッチングによる誤検出
  - Mitigation: コメント・文字列を除外する正規表現パターンを使用

## References

- [LSP textDocument/references](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references) — LSP参照検索の仕様
- `src/solidlsp/ls.py:699-729` — 既存の`request_references`実装
- `src/solidlsp/language_servers/vbscript_lsp/index.py` — 現在のシンボルインデックス実装
