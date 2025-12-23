# Research & Design Decisions

---
**Purpose**: インクルードファイル間の参照追跡機能の設計に関する調査結果と設計判断を記録。

**Usage**:
- ライトディスカバリー実行時の調査結果
- 既存アーキテクチャとの統合ポイント
- 設計判断の根拠
---

## Summary
- **Feature**: include-reference-tracking
- **Discovery Scope**: Extension（既存VBScript LSPへの機能追加）
- **Key Findings**:
  - 既存のASPScriptExtractorはインクルードディレクティブを処理していない
  - SymbolIndexとReferenceTrackerが分離されており、インクルードグラフを追加するレイヤーが明確
  - VBScriptパーサーは行オフセット対応済みで、複数ファイルの位置計算に対応可能

## Research Log

### 既存アーキテクチャ分析
- **Context**: VBScript LSPの現在の構成を把握し、拡張ポイントを特定する
- **Sources Consulted**:
  - `src/solidlsp/language_servers/vbscript_lsp/server.py`
  - `src/solidlsp/language_servers/vbscript_lsp/index.py`
  - `src/solidlsp/language_servers/vbscript_lsp/parser.py`
  - `src/solidlsp/language_servers/vbscript_lsp/asp_extractor.py`
  - `src/solidlsp/language_servers/vbscript_lsp/reference_tracker.py`
- **Findings**:
  - VBScriptLanguageServer: pygls ベースの LSP サーバー、ドキュメントキャッシュ・インデックス管理
  - SymbolIndex: URI/名前による二重インデックス、ReferenceTracker統合済み
  - VBScriptParser: ASP/VBSの判定・パース、行オフセット対応
  - ASPScriptExtractor: `<% %>` と `<script runat="server">` のみ対応、インクルードは未対応
  - ReferenceTracker: 識別子抽出・コメント/文字列除外、定義/参照の区別
- **Implications**:
  - インクルードディレクティブ解析は ASPScriptExtractor の拡張または新モジュールで実装
  - インクルードグラフはSymbolIndexと並列に管理し、find_definition/find_referencesで統合

### Classic ASP インクルード構文
- **Context**: ASP インクルードディレクティブの正確な構文を把握する
- **Sources Consulted**: Microsoft ASP documentation, legacy codebase patterns
- **Findings**:
  - `<!--#include file="path/to/file.asp" -->` - 相対パス（現在ファイルからの相対）
  - `<!--#include virtual="/path/to/file.asp" -->` - 仮想パス（IISルートからの絶対パス）
  - 大文字小文字を区別しない（`FILE`、`File`、`VIRTUAL`等も有効）
  - コメント内でも処理される（HTMLコメントではなくSSIディレクティブ）
  - ファイル拡張子は任意（.asp, .inc, .vbs等）
- **Implications**:
  - 正規表現パターン: `<!--\s*#include\s+(file|virtual)\s*=\s*["']([^"']+)["']\s*-->`
  - パス解決ロジックでfile/virtualを区別する必要あり
  - virtualパス解決にはワークスペースルート設定が必要

### インクルードグラフの表現
- **Context**: ファイル間依存関係のデータ構造を決定
- **Findings**:
  - 有向グラフとして表現（A→Bは「AがBをインクルード」）
  - 推移閉包の計算が必要（A→B→Cの場合、AからCのシンボルにアクセス可能）
  - 循環検出はDFSで実装可能
  - インクリメンタル更新が重要（ファイル変更時に全再計算を避ける）
- **Implications**:
  - `dict[str, list[IncludeEdge]]` 形式で隣接リストを管理
  - 推移閉包はクエリ時に遅延計算（キャッシュ可能）
  - ファイル変更時は該当ファイルのエッジのみ更新、影響範囲の再計算

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| SymbolIndex統合 | SymbolIndexにインクルードグラフを組み込む | 単一コンポーネントで完結 | SymbolIndexの責務過多 | 既存コードへの影響大 |
| 独立モジュール（採用） | IncludeGraphを独立コンポーネントとして実装 | 責務分離、テスト容易 | コンポーネント間連携が必要 | Serenaの設計思想に合致 |
| パーサー拡張 | VBScriptParserにインクルード解析を追加 | パース処理の一元化 | パーサーの肥大化 | インクルードはASP固有 |

## Design Decisions

### Decision: 独立モジュールとしてのIncludeGraph実装
- **Context**: インクルードファイル間の依存関係をどのコンポーネントで管理するか
- **Alternatives Considered**:
  1. SymbolIndexに統合 — 既存の検索ロジックと密結合
  2. 独立モジュール — 新規クラスとして分離
  3. VBScriptParserの拡張 — パース時にインクルード情報も抽出
- **Selected Approach**: 独立モジュール（`IncludeGraph`クラス）として実装
- **Rationale**:
  - 単一責任の原則に従い、インクルード関係の管理を専用コンポーネントに委譲
  - 既存のSymbolIndex/ReferenceTrackerとは疎結合に連携
  - テスト容易性が高い
- **Trade-offs**:
  - コンポーネント間の連携ロジックが必要
  - 複数コンポーネントの状態同期が必要
- **Follow-up**: find_definition/find_references時のグラフ参照実装

### Decision: インクルードディレクティブ解析の実装場所
- **Context**: `<!--#include ...>` の解析をどこで行うか
- **Alternatives Considered**:
  1. ASPScriptExtractor拡張 — 既存クラスにメソッド追加
  2. 新規IncludeParser — インクルード専用パーサー
- **Selected Approach**: 新規`IncludeDirectiveParser`クラス
- **Rationale**:
  - ASPScriptExtractorはVBScriptブロック抽出に特化
  - インクルード解析は異なる関心事（ファイル間依存）
  - 単体テストしやすい
- **Trade-offs**: クラス数増加
- **Follow-up**: ASPファイルオープン時にIncludeDirectiveParserを呼び出す

### Decision: 仮想パス解決のためのワークスペースルート
- **Context**: `#include virtual="/..."` のパス解決にルートディレクトリが必要
- **Alternatives Considered**:
  1. VBScriptLanguageServer初期化時に設定
  2. プロジェクト設定ファイル（.serena/）から読み込み
  3. ワークスペースフォルダからの推測
- **Selected Approach**: VBScriptLanguageServer初期化パラメータとして受け取り、省略時はワークスペースルートを使用
- **Rationale**:
  - LSP初期化時にworkspaceFoldersが利用可能
  - 明示的な設定オプションも提供可能
- **Trade-offs**: 仮想パスのルートが複数ある場合は未対応
- **Follow-up**: 設定パラメータの追加検討

## Risks & Mitigations
- **循環インクルードによる無限ループ** — DFSで訪問済みノードを追跡し、検出時にログ出力して中断
- **大規模プロジェクトでのパフォーマンス** — 推移閉包の遅延計算とキャッシュ、インクリメンタル更新
- **ワークスペース外ファイルの参照** — 該当ファイルは警告付きで無視、シンボル検索結果から除外

## References
- Microsoft Docs: SSI Include Directive — ASP インクルード構文の仕様
- Serena steering: `structure.md` — プロジェクト構成パターン
- 既存実装: `src/solidlsp/language_servers/vbscript_lsp/` — 現在のVBScript LSP
