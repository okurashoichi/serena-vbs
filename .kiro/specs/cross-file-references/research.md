# Research & Design Decisions: cross-file-references

## Summary
- **Feature**: `cross-file-references`
- **Discovery Scope**: Extension（既存のworkspace-initial-scan機能の拡張）
- **Key Findings**:
  - `find_references()`は現在ドキュメントキャッシュ（`_documents`）に依存しているが、`ReferenceTracker`は全インデックスファイルを検索可能
  - Include依存関係は`IncludeGraph.get_transitive_includes()`で取得可能
  - 循環Include検出機能が既存（`IncludeGraph.has_cycle()`）

## Research Log

### 現在の参照検索アーキテクチャ
- **Context**: 要件1（全インデックスファイルからの参照検索）を実現するための既存実装調査
- **Sources Consulted**: server.py, index.py, reference_tracker.py
- **Findings**:
  - `VBScriptLanguageServer.find_references()` (server.py:401-425)は`self._documents`キャッシュの存在チェックを行うが、`SymbolIndex.find_references()`自体は全インデックスファイルを検索可能
  - `ReferenceTracker._references_by_name`は大文字小文字を区別せず検索（VBScript仕様準拠）
  - `include_declaration`パラメータで定義箇所の包含/除外を制御可能
- **Implications**: `find_references()`の実装変更は最小限で済む。`_documents`キャッシュ依存を除去するだけで要件1を満たせる

### Include依存関係の活用方法
- **Context**: 要件2（Include経由の参照検索）を実現するための既存機能調査
- **Sources Consulted**: include_graph.py, server.py（goto_definition部分）
- **Findings**:
  - `IncludeGraph.get_transitive_includes(uri)`で推移的Include関係を取得可能
  - `IncludeGraph.get_includers(uri)`で逆方向（どのファイルがIncludeしているか）も取得可能
  - 循環Includeは`visited`セットで既に対処済み（無限ループ防止）
  - `goto_definition()`が既にInclude経由の検索を実装済み（server.py:373-397）
- **Implications**: Include依存関係を考慮した参照検索は、`goto_definition()`のパターンを参考に実装可能。ただし参照検索の場合は「どのファイルからも参照を検索」が必要なため、スコープ制限の方向が異なる

### パフォーマンス考慮事項
- **Context**: 要件4（1000ファイルで1秒以内）を満たすための設計検討
- **Sources Consulted**: reference_tracker.py, index.py
- **Findings**:
  - `ReferenceTracker._references_by_name`は`dict[str, list[Reference]]`で、シンボル名でO(1)ルックアップ
  - 既存のインデックス構造を活用するため、参照検索時の追加スキャンは不要
  - 重複除去には`set`ベースのLocationハッシュが必要
- **Implications**: 既存のインデックス構造が効率的なため、パフォーマンス目標は達成可能。重複除去のために`Reference`または`Location`のハッシュ実装が必要

### 参照結果の重複可能性
- **Context**: 要件3.4（重複なし返却）を満たすための調査
- **Sources Consulted**: reference_tracker.py, reference.py
- **Findings**:
  - 現在の`ReferenceTracker.find_references()`は重複チェックを行っていない
  - `Reference`クラスは`@dataclass`だが`__hash__`は未定義
  - 同一シンボルが複数回登場する場合（例：同一行で複数回呼び出し）は、それぞれ別の参照として記録される（これは正しい動作）
- **Implications**: Include経由の検索で複数パスから同一ファイルに到達した場合の重複は発生しない（`_references_by_name`は一意）。ただし、将来的な拡張で重複が発生する可能性がある場合は、Location単位での重複除去を実装すべき

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 既存ReferenceTracker活用 | 現在のインデックス構造をそのまま利用 | 最小変更、パフォーマンス良好 | Include考慮が必要な場合に追加ロジック必要 | 採用 |
| スコープ付き参照検索 | Include依存関係に基づくスコープ制限 | ASPプロジェクトの可視性ルールに準拠 | 複雑性増加、全ファイル検索との使い分けが必要 | 要件2で必要に応じて検討 |

## Design Decisions

### Decision: 全インデックスファイルからの直接検索
- **Context**: 要件1「全インデックス済みファイルから該当シンボルの参照を返却」の実現方法
- **Alternatives Considered**:
  1. `find_references()`内で全URIをスコープとして渡す
  2. `ReferenceTracker.find_references()`をそのまま利用（スコープ制限なし）
- **Selected Approach**: オプション2。`ReferenceTracker`は既に全インデックスファイルを対象に検索するため、`_documents`キャッシュの存在チェックを除去するだけで良い
- **Rationale**: 既存実装が要件を満たしており、追加コードが最小限
- **Trade-offs**: Include依存関係の考慮は別途対応が必要
- **Follow-up**: 要件2のInclude依存関係対応と統合

### Decision: Include依存関係の検索スコープ
- **Context**: 要件2「Include経由で参照可能なファイルからも参照を検索」の解釈と実装方針
- **Alternatives Considered**:
  1. Include依存関係に基づくスコープ制限（カレントファイルからIncludeで到達可能なファイルのみ検索）
  2. 全インデックスファイルから検索し、Include関係はメタデータとして提供
  3. 全インデックスファイルから検索（Include関係は参照検索では考慮しない）
- **Selected Approach**: オプション3。参照検索は「このシンボルがどこで使われているか」を調べるものであり、Include可視性ルールとは独立
- **Rationale**:
  - 定義ジャンプ（`goto_definition`）はInclude可視性に基づくべき（呼び出し元から見える定義を探す）
  - 参照検索（`find_references`）はプロジェクト全体で「このシンボルがどこで使われているか」を調べるべき
  - リファクタリング時には全参照箇所を知る必要がある
- **Trade-offs**: Include経由で本来見えないはずのシンボルへの参照も表示される
- **Follow-up**: 必要に応じて将来的にフィルタリングオプションを追加

### Decision: 重複除去の実装箇所
- **Context**: 要件3.4「参照結果を重複なく返却」の実装方針
- **Alternatives Considered**:
  1. `Reference`クラスに`__hash__`と`__eq__`を追加し、`set`で重複除去
  2. `find_references()`戻り値を`Location`単位で重複除去
  3. 現状維持（重複は発生しない前提）
- **Selected Approach**: オプション3を基本とし、必要に応じてオプション2を追加
- **Rationale**: 現在の`ReferenceTracker`実装では、同一シンボルの同一位置への重複登録は発生しない。ただし、防御的プログラミングとしてLocation単位の重複チェックを追加
- **Trade-offs**: 追加の処理コストは最小限
- **Follow-up**: テストで重複シナリオを確認

## Risks & Mitigations
- **リスク1**: 大規模プロジェクトでのパフォーマンス劣化 — `_references_by_name`のO(1)ルックアップと既存インデックス活用で対応
- **リスク2**: Include可視性ルールとの不整合 — 要件の解釈を明確化（参照検索は全ファイル対象）、必要に応じて将来拡張
- **リスク3**: `_documents`キャッシュ除去による副作用 — `_documents`は単なるキャッシュであり、インデックスは独立して管理されているため影響なし

## References
- [LSP textDocument/references仕様](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references)
- workspace-initial-scan design.md — インデックス構造とワークスペーススキャン設計
