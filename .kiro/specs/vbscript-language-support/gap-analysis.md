# Gap Analysis: vbscript-language-support

## 1. 現状調査

### 1.1 既存のコードベース資産

#### 発見されたVBScript関連資産
| 資産 | 状態 | 備考 |
|------|------|------|
| `src/solidlsp/language_servers/vbscript_lsp/` | 空（__pycache__のみ） | ディレクトリ構造のみ存在 |
| `test/resources/repos/vbscript/test_repo/` | 存在（.serena設定あり） | テストリポジトリ準備済み |
| `test/resources/repos/asp/test_repo/` | 存在（空） | ASPテストリポジトリ準備済み |
| `ls_config.py` Language enum | VBSCRIPTなし | 登録が必要 |
| `pyproject.toml` markers | vbscriptマーカーなし | 登録が必要 |

#### 既存の言語サーバー実装パターン
`BashLanguageServer`を参考パターンとして特定：
- `SolidLanguageServer`を継承
- `_setup_runtime_dependencies()`: npm経由で依存関係をインストール
- `_get_initialize_params()`: LSP初期化パラメータを定義
- `_start_server()`: サーバー起動と初期化ハンドシェイク

### 1.2 外部依存関係調査結果

**重要な発見**: VBScript専用のLSP実装は存在しない

| 調査項目 | 結果 |
|----------|------|
| npm vbscript-language-server | 存在しない |
| GitHub VBScript LSP | 専用実装なし |
| VS Code拡張 [asp-classic-support](https://github.com/zbecknell/asp-classic-support) | 構文ハイライト＋基本インテリセンス（LSPではない） |
| [pygls](https://github.com/openlawlibrary/pygls) | Pythonで独自LSPを構築可能なフレームワーク |

### 1.3 コンベンションと統合ポイント

#### ファイル構成パターン
```
src/solidlsp/language_servers/
├── {lang}_language_server.py  # メインクラス
├── {lang}_lsp/                # 言語固有のリソース（オプション）
│   └── config.py              # 設定ファイル（オプション）
└── common.py                  # RuntimeDependency共通ユーティリティ
```

#### 登録必要箇所
1. `ls_config.py`: `Language` enum に `VBSCRIPT` を追加
2. `ls_config.py`: `get_source_fn_matcher()` に `.vbs`, `.asp`, `.inc` を追加
3. `ls_config.py`: `get_ls_class()` に `VBScriptLanguageServer` を追加
4. `pyproject.toml`: pytest markers に `vbscript` を追加

---

## 2. 要件実現可能性分析

### 要件とアセットのマッピング

| 要件 | 技術ニーズ | ギャップ状況 |
|------|-----------|-------------|
| Req1: 言語設定追加 | Language enum, FilenameMatcher | **実装必要** - パターン明確 |
| Req2: LSP実装 | SolidLanguageServer継承クラス | **重大なギャップ** - 外部LSPが存在しない |
| Req3: 依存関係管理 | RuntimeDependencyCollection | **Research Needed** - 独自LSPの場合不要 |
| Req4: VBScript固有設定 | is_ignored_dirname, encoding | **実装必要** - パターン明確 |
| Req5: テスト/ドキュメント | pytest marker, test repo | **部分的に準備済み** |

### 複雑性シグナル

- **外部統合**: 外部LSPが存在しないため、独自実装が必要
- **アルゴリズムロジック**: VBScript構文解析が必要
- **既存パターン**: 他の言語サーバー実装パターンは明確

---

## 3. 実装アプローチオプション

### Option A: 既存の外部LSPを使用（推奨されない）

**理由**: VBScript専用の外部LSPは存在しない

**Trade-offs**:
- ❌ 実現不可能 - 該当する外部LSPが存在しない

---

### Option B: pygls を使用した独自LSP構築

**概要**: [pygls](https://pygls.readthedocs.io/en/stable/)フレームワークを使用してPythonでカスタムVBScript LSPを構築

**必要な作業**:
1. VBScript構文パーサーの実装（正規表現 or ANTLRベース）
2. pygls上にLSPサーバーを構築
3. `documentSymbol`, `definition`, `references`の実装
4. Serenaの`SolidLanguageServer`との統合

**Trade-offs**:
- ✅ 完全なコントロール - 必要な機能のみ実装
- ✅ Pythonエコシステム内で完結
- ✅ 外部プロセス起動が不要（オプション）
- ❌ 大幅な開発工数が必要
- ❌ VBScript構文解析の専門知識が必要
- ❌ メンテナンス負担

**複雑性**: XL（2週間以上）

---

### Option C: 簡易的なシンボル抽出実装（ハイブリッド）

**概要**: 外部LSPを使用せず、正規表現ベースのシンプルなシンボル抽出を`SolidLanguageServer`内に直接実装

**必要な作業**:
1. `VBScriptLanguageServer`クラスを作成
2. `request_document_symbols()`をオーバーライドして独自パーサーを使用
3. LSPプロセスなしでシンボル情報を返す
4. `definition`/`references`は独自ロジックで実装

**Trade-offs**:
- ✅ 最小限の外部依存
- ✅ 開発工数を抑制可能（正規表現ベース）
- ✅ 既存パターンとの整合性を維持
- ❌ LSP標準機能の一部が利用不可
- ❌ 複雑なVBScript構文への対応が限定的

**複雑性**: M-L（1-2週間）

---

### Option D: 既存VS Code拡張のTextMate grammarを活用

**概要**: [asp-classic-support](https://github.com/zbecknell/asp-classic-support)のTextMate grammarを参考に構文解析を実装

**必要な作業**:
1. TextMate grammar定義を分析
2. トークンパターンをPythonに移植
3. シンボル抽出ロジックを構築

**Trade-offs**:
- ✅ 実績のある構文定義を活用
- ✅ ASPファイル内のVBScriptにも対応
- ❌ TextMate grammarからの変換作業が必要
- ❌ LSP機能は独自実装

**複雑性**: M（3-7日）

---

## 4. 工数とリスク評価

| オプション | 工数 | リスク | 推奨度 |
|-----------|------|--------|--------|
| Option A | - | - | ❌ 不可 |
| Option B (pygls) | XL | High | △ 長期的には良いが工数大 |
| Option C (簡易実装) | M-L | Medium | ◎ 推奨 |
| Option D (TextMate) | M | Medium | ○ 代替案として有効 |

### リスク要因
- **High**: 完全なLSP仕様準拠が必要な場合、独自パーサーの品質問題
- **Medium**: VBScript構文の複雑さ（特にASP埋め込み）、エンコーディング問題

---

## 5. 設計フェーズへの推奨事項

### 推奨アプローチ: Option C（簡易的なシンボル抽出実装）

**理由**:
1. VBScriptは主にレガシーコードの保守・移行用途であり、完全なLSP機能は不要
2. 既存のSerena言語サーバーパターンとの整合性を維持
3. 適度な工数で実用的な機能を提供可能

### 設計フェーズで調査が必要な項目

| 項目 | 内容 |
|------|------|
| **Research Needed: VBScript構文仕様** | Function/Sub/Class/Property定義のパターン |
| **Research Needed: ASP埋め込み** | `<% %>`, `<script runat="server">`の解析方法 |
| **Research Needed: エンコーディング** | Shift_JIS/CP932対応の実装方法 |
| **検討: 外部プロセス** | LSPサーバーを別プロセスで起動するか、インプロセスか |

### 重要な設計判断

1. **LSPプロセスの有無**: 外部LSPプロセスなしで`SolidLanguageServer`の機能をオーバーライドする方式を推奨
2. **パーサー実装**: 正規表現ベースの軽量パーサーから開始し、必要に応じて拡張
3. **機能スコープ**: まずは`documentSymbol`（シンボル一覧）に注力し、`definition`/`references`は段階的に追加

---

## Sources

- [pygls - Python Language Server Framework](https://github.com/openlawlibrary/pygls)
- [pygls Documentation](https://pygls.readthedocs.io/en/stable/)
- [asp-classic-support VS Code Extension](https://github.com/zbecknell/asp-classic-support)
- [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)
