# Research & Design Decisions: vbscript-language-support

---
**Purpose**: VBScript言語サポート実装に必要な調査結果と設計判断の記録

**Updated**: ユーザーフィードバックに基づき、pygls使用の独自LSP構築アプローチに変更

---

## Summary
- **Feature**: `vbscript-language-support`
- **Discovery Scope**: Complex Integration（独自LSPサーバー構築）
- **Key Findings**:
  - VBScript専用の外部LSP実装は存在しない → **pygls**を使用して独自LSPサーバーを構築
  - pygls v2.0.0はPythonで完全なLSPサーバーを「数行のコードで」構築可能
  - 既存の`SolidLanguageServer`パターンは外部プロセスとの通信に対応済み

## Research Log

### VBScript LSP の存在調査
- **Context**: 要件2で外部LSPプロセスの起動が求められているため、利用可能なLSPを調査
- **Sources Consulted**:
  - npm registry検索
  - GitHub topics/repositories検索
  - [asp-classic-support VS Code拡張](https://github.com/zbecknell/asp-classic-support)
- **Findings**:
  - npm: `vbscript-language-server` パッケージは存在しない
  - GitHub: VBScript専用のLSP実装プロジェクトは見つからない
  - VS Code拡張: asp-classic-supportは構文ハイライト＋基本インテリセンスのみ（LSPではない）
- **Implications**: 外部LSPに依存する設計は不可能 → **pygls**を使用して独自LSPサーバーを構築

### pygls フレームワーク調査
- **Context**: 独自LSPサーバー構築のためのフレームワーク選定
- **Sources Consulted**:
  - [pygls Documentation v2.0.0](https://pygls.readthedocs.io/en/stable/)
  - [pygls GitHub](https://github.com/openlawlibrary/pygls)
  - [pygls Document & Workspace Symbols Example](https://pygls.readthedocs.io/en/latest/servers/examples/symbols.html)
  - [pygls Goto and Find References Example](https://pygls.readthedocs.io/en/latest/servers/examples/goto.html)
- **Findings**:
  - **pygls v2.0.0**: Pythonで完全なLSPサーバーを構築可能
  - **通信方式**: STDIO、TCP/IP、WEBSOCKET対応
  - **プログラミングスタイル**: 同期・非同期の両対応
  - **実装パターン**: `@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)` デコレータで機能登録
  - **documentSymbol**: 階層構造のシンボル情報を返す実装例あり
  - **definition/references**: カーソル位置から単語を抽出し、インデックスを検索して結果を返す
- **Implications**:
  - pygls上に完全なVBScript LSPサーバーを構築可能
  - 標準LSPプロトコルに準拠した実装が可能
  - Pythonエコシステム内で完結（新たな言語不要）

### pygls LSP実装パターン
- **Context**: 具体的な実装方法の把握
- **Sources Consulted**:
  - [pygls symbols.py example](https://github.com/openlawlibrary/pygls/blob/main/examples/servers/symbols.py)
  - [pygls goto.py example](https://github.com/openlawlibrary/pygls/blob/main/examples/servers/goto.py)
- **Findings**:
  ```python
  from lsprotocol import types
  from pygls.lsp.server import LanguageServer

  server = LanguageServer("vbscript-lsp", "v1.0.0")

  @server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
  def document_symbol(ls, params: types.DocumentSymbolParams):
      # シンボル抽出ロジック
      return [types.DocumentSymbol(...)]

  @server.feature(types.TEXT_DOCUMENT_DEFINITION)
  def goto_definition(ls, params: types.DefinitionParams):
      # 定義位置を返す
      return types.Location(...)

  @server.feature(types.TEXT_DOCUMENT_REFERENCES)
  def find_references(ls, params: types.ReferenceParams):
      # 参照位置のリストを返す
      return [types.Location(...)]
  ```
- **Implications**:
  - 各LSP機能は独立したハンドラ関数として実装
  - `lsprotocol`モジュールで型定義を利用可能
  - シンボルインデックスを構築してクエリに応答するパターン

### VBScript構文仕様
- **Context**: シンボル抽出のために解析すべき構文を特定
- **Sources Consulted**:
  - [VBScript Class Objects - TutorialsPoint](https://www.tutorialspoint.com/vbscript/vbscript_class_objects.htm)
  - [Sub - VBScript - SS64.com](https://ss64.com/vb/sub.html)
  - [DevGuru VBScript Reference](https://www.devguru.com/content/technologies/vbscript/objects-class.html)
- **Findings**:
  - **Function**: `[Public|Private] Function name(arglist) ... End Function`
  - **Sub**: `[Public|Private] Sub name(arglist) ... End Sub`
  - **Class**: `Class name ... End Class`
  - **Property Get/Let/Set**: `[Public|Private] Property Get|Let|Set name(arglist) ... End Property`
  - **Const**: `[Public|Private] Const name = value`
  - **Dim**: `[Public|Private] Dim name`
- **Implications**: 正規表現ベースのパーサーで十分対応可能。大文字小文字を区別しない（case-insensitive）必要あり

### ASPファイル内のVBScript埋め込み
- **Context**: Classic ASPファイル（.asp）内のVBScriptを解析する方法
- **Sources Consulted**:
  - Classic ASP仕様
  - asp-classic-support TextMate grammar
- **Findings**:
  - `<% ... %>`: サーバーサイドスクリプトブロック
  - `<%= ... %>`: 出力式
  - `<script language="vbscript" runat="server"> ... </script>`: 代替形式
  - HTMLコンテキストとVBScriptコンテキストの分離が必要
- **Implications**: ASPファイルは前処理でVBScriptブロックを抽出し、その中のシンボルを解析する2段階アプローチが必要

### エンコーディング対応
- **Context**: レガシーVBScriptコードベースは日本語環境でShift_JIS/CP932が多い
- **Sources Consulted**:
  - Python codecs documentation
  - 既存のSerena encoding処理（`LanguageServerConfig.encoding`）
- **Findings**:
  - `LanguageServerConfig`にはすでに`encoding`フィールドが存在
  - Pythonの`codecs`モジュールでShift_JIS対応可能
  - `.serena/`設定でプロジェクト単位のエンコーディング指定が可能
- **Implications**: 既存のエンコーディング機構を活用し、デフォルトをUTF-8、設定でShift_JIS等に変更可能とする

### 既存言語サーバーパターン分析
- **Context**: Serenaの他言語実装パターンを把握
- **Sources Consulted**:
  - `src/solidlsp/language_servers/bash_language_server.py`
  - `src/solidlsp/ls_config.py`
  - `src/solidlsp/ls.py`
- **Findings**:
  - **継承パターン**: `SolidLanguageServer`を継承
  - **必須メソッド**: `_setup_runtime_dependencies()`, `_get_initialize_params()`, `_start_server()`
  - **登録箇所**: `Language` enum, `get_source_fn_matcher()`, `get_ls_class()`
  - **外部プロセス起動**: `ProcessLaunchInfo`で外部LSPプロセスを起動
- **Implications**:
  - pygls LSPサーバーを外部プロセスとして起動
  - 既存の`RuntimeDependencyCollection`パターンで自動インストール可能

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| A: 外部LSP使用 | 既存のVBScript LSPを起動 | 標準LSPプロトコル準拠 | **不可能** - 該当LSPが存在しない | - |
| **B: pygls独自LSP** | pygls上にフルLSPサーバー構築 | 完全なLSP機能、標準準拠 | 開発工数M-L | **採用** |
| C: 簡易パーサー内蔵 | 正規表現ベースのシンボル抽出 | 最小工数 | LSP標準機能一部制限 | 却下 |
| D: TextMate活用 | asp-classic-supportのgrammar移植 | 実績ある構文定義 | 変換作業が必要 | 参考として活用 |

## Design Decisions

### Decision: pygls使用の独自LSPサーバー構築

- **Context**: 要件2では外部LSPプロセスの起動を想定しているが、VBScript用LSPは存在しない
- **Alternatives Considered**:
  1. `SolidLanguageServer`の`request_document_symbols()`をオーバーライドして独自パーサー使用（工数S-M）
  2. pygls上にフルLSPサーバーを構築（工数M-L）
  3. 機能を諦めてサポート対象外とする
- **Selected Approach**: Option 2 - pygls上に完全なLSPサーバーを構築
- **Rationale**:
  - ユーザーからの明示的な要望（「自作でLSPを作成したい」）
  - 標準LSPプロトコルに完全準拠
  - 将来の機能拡張（診断、コード補完等）が容易
  - Pythonエコシステム内で完結
- **Trade-offs**:
  - ✅ 完全なLSP機能（documentSymbol, definition, references等）
  - ✅ 標準プロトコル準拠で他ツールとの互換性
  - ✅ 将来の機能拡張が容易
  - ❌ 初期開発工数が増加（M-L）
  - ❌ 新たな依存関係（pygls, lsprotocol）
- **Follow-up**: LSPサーバーはSTDIO通信モードで起動

### Decision: LSPサーバーの配置と起動方式

- **Context**: pygls LSPサーバーをどこに配置し、どう起動するか
- **Alternatives Considered**:
  1. 別リポジトリで開発し、pipでインストール
  2. Serenaリポジトリ内に配置し、`RuntimeDependencyCollection`で管理
  3. Serenaに同梱（サブパッケージ）
- **Selected Approach**: Option 3 - Serenaリポジトリ内のサブパッケージとして配置
- **Rationale**:
  - VBScript LSPはSerena専用であり、汎用性は低い
  - 依存関係管理が簡素化
  - テストとメンテナンスが容易
- **Trade-offs**:
  - ✅ シンプルな依存関係
  - ✅ 一体的な開発・テスト
  - ❌ Serena本体のサイズ増加
- **Follow-up**: `src/solidlsp/language_servers/vbscript_lsp/`に配置

### Decision: シンボル種別の優先順位

- **Context**: VBScriptには多くの構文要素があるが、すべてをサポートする必要はない
- **Alternatives Considered**:
  1. 全構文要素をサポート
  2. 主要構文のみ段階的にサポート
- **Selected Approach**: Option 2 - 主要構文を優先
- **Rationale**: レガシーコード保守・移行の主要ユースケースに焦点
- **Trade-offs**:
  - ✅ 初期リリースを早期化
  - ❌ 一部の構文は未サポート
- **Follow-up**:
  - Phase 1: Function, Sub, Class, Property (Get/Let/Set)
  - Phase 2: Const, Dim (モジュールレベル)
  - Phase 3: 必要に応じて拡張

### Decision: ASPファイル解析アプローチ

- **Context**: .aspファイルにはHTML + VBScript + CSSなど複数言語が混在
- **Alternatives Considered**:
  1. ASPファイル全体をVBScriptとして解析
  2. VBScriptブロック（`<% %>`）のみを抽出して解析
  3. ASPファイルを別言語として扱う
- **Selected Approach**: Option 2 - VBScriptブロック抽出方式
- **Rationale**:
  - HTMLコンテキストでの誤検出を防止
  - シンボル位置（行番号）を正確に保持
- **Trade-offs**:
  - ✅ 精度の高いシンボル抽出
  - ❌ 前処理ロジックが必要
- **Follow-up**: インラインスクリプト(`<%= %>`)は式のみなのでシンボル抽出対象外

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| pygls依存関係の追加 | パッケージサイズ増加 | pyglsは軽量（~100KB）、許容範囲内 |
| VBScript構文の複雑なエッジケース | 正規表現パーサーで誤検出・漏れ | テストケースを充実させ、段階的に改善 |
| ASP埋め込みの行番号ずれ | シンボル位置が不正確 | オフセット計算を慎重に実装 |
| レガシーエンコーディング | ファイル読み込みエラー | 設定可能なエンコーディング、エラーハンドリング |
| LSPサーバープロセス管理 | プロセスリーク | 既存の言語サーバー管理パターンを踏襲 |

## References

- [pygls Documentation v2.0.0](https://pygls.readthedocs.io/en/stable/) - Python LSPフレームワーク
- [pygls GitHub](https://github.com/openlawlibrary/pygls) - ソースコードと例
- [pygls Document & Workspace Symbols](https://pygls.readthedocs.io/en/latest/servers/examples/symbols.html) - シンボル実装例
- [pygls Goto and Find References](https://pygls.readthedocs.io/en/latest/servers/examples/goto.html) - 定義/参照実装例
- [VBScript Class Objects - TutorialsPoint](https://www.tutorialspoint.com/vbscript/vbscript_class_objects.htm) - VBScript構文リファレンス
- [Sub - VBScript - SS64.com](https://ss64.com/vb/sub.html) - Sub/Function構文詳細
- [asp-classic-support](https://github.com/zbecknell/asp-classic-support) - VS Code拡張（TextMate grammar参考）
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) - LSP仕様
