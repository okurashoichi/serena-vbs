# Research & Design Decisions: workspace-initial-scan

---
**Purpose**: VBScript LSPワークスペース初期スキャン機能の設計調査結果

---

## Summary
- **Feature**: `workspace-initial-scan`
- **Discovery Scope**: Extension（既存システムの拡張）
- **Key Findings**:
  - Pyrightパターン（`analysis_complete` + `completions_available`）が参考実装として最適
  - `server.py`の`_open_document()`を内部的に再利用可能
  - 外部依存なし（標準ライブラリのみ）

## Research Log

### Pyrightの初期スキャンパターン
- **Context**: 他の言語サーバーがどのようにワークスペーススキャンを実装しているか調査
- **Sources Consulted**:
  - `src/solidlsp/language_servers/pyright_server.py:43-196`
  - `src/solidlsp/language_servers/solargraph.py:50-367`
  - `src/solidlsp/language_servers/ruby_lsp.py:40-432`
- **Findings**:
  - `threading.Event`を使用した完了通知パターンが標準
  - `analysis_complete`と`completions_available`の2つのイベントを持つ
  - ログメッセージ監視で完了検出（`Found N source files`パターン）
  - タイムアウト付きwait（Pyright: 5秒、Solargraph: 60秒、Ruby LSP: 30秒）
- **Implications**: VBScriptでも同様のパターンを採用

### VBScript LSP現状構造
- **Context**: 既存実装の拡張ポイント特定
- **Sources Consulted**:
  - `src/solidlsp/language_servers/vbscript_lsp/server.py`
  - `src/solidlsp/language_servers/vbscript_language_server.py`
- **Findings**:
  - `VBScriptLanguageServer`クラス（server.py）がpyglsベースのLSPサーバー
  - `__init__`に`workspace_root`パラメータが既に存在
  - `_open_document(uri, content)`が既存のインデックス登録処理を担当
  - `IGNORED_DIRS`が`vbscript_language_server.py:29`で定義済み
- **Implications**: 最小限の変更で機能追加可能

### ファイルエンコーディング
- **Context**: VBScript/ASPファイルのエンコーディング対応
- **Sources Consulted**: Python標準ライブラリドキュメント
- **Findings**:
  - VBScriptファイルはShift-JIS（Windows-31J）またはUTF-8が一般的
  - Pythonの`open()`はデフォルトでシステムエンコーディングを使用
  - `errors='replace'`または`errors='ignore'`でエラー回避可能
- **Implications**: UTF-8をデフォルト、Shift-JISをフォールバックとして実装

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| A: server.py拡張 | `_scan_workspace()`メソッド追加 | 最小変更、Pyrightパターン踏襲 | 責務増加 | **採用** |
| B: WorkspaceScanner分離 | 新クラス作成 | 関心分離、テスト容易 | ファイル増加、複雑化 | 将来検討 |
| C: ハイブリッド | プライベート関数として実装 | シンプル | 中途半端 | 非採用 |

## Design Decisions

### Decision: スキャン実行タイミング
- **Context**: いつワークスペーススキャンを実行するか
- **Alternatives Considered**:
  1. `__init__`終了前 — 同期的に完了
  2. LSP initialize後 — クライアントから呼び出し
  3. バックグラウンドスレッド — 非同期実行
- **Selected Approach**: `__init__`終了前に同期実行
- **Rationale**: LSPリクエスト受付前にインデックス構築が完了している必要がある
- **Trade-offs**: 起動時間が若干増加するが、機能の確実性を優先
- **Follow-up**: 大規模プロジェクトでの起動時間計測

### Decision: 完了通知メカニズム
- **Context**: スキャン完了をどのように通知するか
- **Alternatives Considered**:
  1. `threading.Event` — Pyrightパターン
  2. コールバック関数 — 柔軟だが複雑
  3. ポーリング — 非効率
- **Selected Approach**: `threading.Event`（`analysis_complete`）
- **Rationale**: 既存の言語サーバー実装と一貫性を保つ
- **Trade-offs**: イベントベースで若干の複雑性があるが、他の実装との整合性を優先
- **Follow-up**: なし

### Decision: エンコーディング戦略
- **Context**: VBScript/ASPファイルのエンコーディング対応
- **Alternatives Considered**:
  1. UTF-8固定 — シンプルだが日本語環境で問題
  2. Shift-JIS固定 — レガシー対応だがUTF-8で問題
  3. 自動検出 — 複雑だが汎用的
  4. UTF-8優先、フォールバックでShift-JIS — バランス型
- **Selected Approach**: UTF-8優先、`errors='replace'`でエラー回避
- **Rationale**: 多くのモダン環境でUTF-8が標準、エラー時は置換で継続
- **Trade-offs**: 一部文字化けの可能性があるが、スキャン失敗よりも継続を優先
- **Follow-up**: 実運用で問題があれば自動検出を検討

## Risks & Mitigations
- **大規模プロジェクトでのパフォーマンス** — 1000ファイル超で警告ログ、将来的に非同期化検討
- **パースエラーによるスキャン中断** — 既存のtry-catchパターン適用、個別ファイルエラーは継続
- **メモリ使用量増加** — インデックスサイズは既存設計に依存、監視のみ

## References
- [Python pathlib](https://docs.python.org/3/library/pathlib.html) — ファイルパス操作
- [Python os.walk](https://docs.python.org/3/library/os.html#os.walk) — ディレクトリ走査
- [pygls Documentation](https://pygls.readthedocs.io/) — pyglsフレームワーク
- Pyright Server実装 (`pyright_server.py`) — 参考パターン
