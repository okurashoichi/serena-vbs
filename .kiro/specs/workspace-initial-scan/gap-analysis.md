# Implementation Gap Analysis: workspace-initial-scan

## 1. 現状調査

### 既存アセット

| ファイル | 役割 | 関連性 |
|---------|------|--------|
| `vbscript_lsp/server.py` | VBScript LSPサーバー本体 | **直接変更対象** |
| `vbscript_lsp/index.py` | シンボルインデックス管理 | 既存機能を活用 |
| `vbscript_lsp/parser.py` | VBScriptパーサー | 既存機能を活用 |
| `vbscript_language_server.py` | Serena-LSP統合ラッパー | 変更不要（LSP外部IF） |
| `pyright_server.py` | 参考実装（Pyright） | パターン参照 |

### 既存パターン

**ドキュメント処理フロー（現状）**:
```
ファイルオープン → _open_document() → _update_index() → SymbolIndex.update()
                                    → _update_includes() → IncludeGraph.update()
```

**VBScriptLanguageServerクラス構成**:
- `self._parser`: VBScriptParser（シンボル抽出）
- `self._index`: SymbolIndex（シンボル検索）
- `self._documents`: dict[str, str]（開いたドキュメントのキャッシュ）
- `self._include_graph`: IncludeGraph（include追跡）
- `self._include_parser`: IncludeDirectiveParser

### 統合サーフェス

**ワークスペースルート取得**:
- `__init__`に`workspace_root`パラメータが既に存在
- 現状はinclude解決のみに使用

**除外ディレクトリ**:
- `vbscript_language_server.py:29`で`IGNORED_DIRS`が定義済み
- `.git`, `node_modules`, `Backup`, `bin`, `obj`

---

## 2. 要件実現可能性分析

### 要件 → 技術ニーズマッピング

| 要件ID | 技術ニーズ | 既存資産 | ギャップ |
|--------|-----------|---------|---------|
| 1.1 | ワークスペース再帰探索 | なし | **Missing**: os.walk実装 |
| 1.2 | 拡張子フィルタリング | `ls_config.py:176-177`に定義済み | なし |
| 1.3-1.4 | 除外ディレクトリ | `IGNORED_DIRS`定義済み | なし |
| 2.1-2.2 | ファイル読み込み・パース | `_update_index()`が利用可能 | **Missing**: ファイル読み込みメソッド |
| 2.3-2.4 | エラーハンドリング | `_update_index()`でtry-catch済み | なし |
| 3.1 | ログ出力 | logger利用可能 | なし |
| 3.2 | 完了フラグ | なし | **Missing**: `threading.Event`追加 |
| 4.1-4.3 | 既存機能統合 | `SymbolIndex`が対応 | なし |
| 5.1-5.3 | パフォーマンス | 検証必要 | **Research Needed** |

### 複雑性シグナル

- **タイプ**: 既存拡張（Extension）
- **複雑性**: 中程度
  - 新規ロジック: ファイルシステム走査のみ
  - 既存パーサー・インデックスを再利用
  - 外部依存なし（標準ライブラリのみ）

---

## 3. 実装アプローチオプション

### Option A: VBScriptLanguageServer（server.py）を拡張

**変更内容**:
1. `_scan_workspace()`メソッド追加
2. `__init__`から呼び出し
3. `analysis_complete`イベント追加

**該当ファイル**:
```
src/solidlsp/language_servers/vbscript_lsp/server.py
```

**トレードオフ**:
- ✅ 最小限の変更
- ✅ 既存の`_update_index()`を直接再利用
- ✅ Pyrightパターンに近い構造
- ❌ server.pyの責務がやや増加

### Option B: 新規WorkspaceScannerクラス作成

**変更内容**:
1. `workspace_scanner.py`新規作成
2. スキャンロジックを分離
3. server.pyから呼び出し

**該当ファイル**:
```
src/solidlsp/language_servers/vbscript_lsp/workspace_scanner.py (新規)
src/solidlsp/language_servers/vbscript_lsp/server.py (小変更)
```

**トレードオフ**:
- ✅ 関心の分離
- ✅ 単体テストが容易
- ❌ ファイル数増加
- ❌ クラス間のやり取りが複雑化

### Option C: ハイブリッドアプローチ

**変更内容**:
1. スキャンロジックを`server.py`内のプライベート関数として実装
2. 将来的に分離可能な設計
3. 設定クラス追加（拡張子、除外ディレクトリ）

**トレードオフ**:
- ✅ 初期実装がシンプル
- ✅ 必要に応じてリファクタリング可能
- ❌ 中途半端な分離

---

## 4. 推奨アプローチ

### 推奨: **Option A（server.py拡張）**

**理由**:
1. **Pyrightパターンとの一貫性**: 他の言語サーバー実装と同じ構造
2. **変更範囲の最小化**: 1ファイルのみ変更
3. **既存メソッドの再利用**: `_open_document()`を内部的に呼び出すだけ
4. **テスト容易性**: 既存テストインフラを活用可能

### 設計上の決定事項

| 決定事項 | 選択 | 根拠 |
|---------|------|------|
| スキャン実行タイミング | `__init__`終了前 | LSPリクエスト受付前に完了必要 |
| スキャン方式 | 同期（ブロッキング） | 非同期は複雑性が増す、初回のみ |
| 完了通知 | `threading.Event` | Pyrightと同パターン |
| ログ形式 | `Found N source files` | Pyrightと同パターン |
| 拡張子定義 | 定数として定義 | 再利用性・可読性 |

---

## 5. 実装複雑性とリスク

### 工数見積もり: **S（1-3日）**

**根拠**:
- 既存パターンの拡張
- 標準ライブラリのみ使用
- 明確なスコープ
- 既存テストリポジトリが利用可能

### リスク: **Low**

| リスク | 緩和策 |
|-------|--------|
| 大規模プロジェクトでのパフォーマンス | 警告ログ、将来的な非同期化検討 |
| パースエラーによるスキャン中断 | 既存のtry-catchパターン適用 |
| エンコーディング問題 | UTF-8/Shift-JIS対応確認必要 |

---

## 6. 設計フェーズへの引き継ぎ事項

### 確定事項
- Option Aで実装
- `server.py`に`_scan_workspace()`メソッド追加
- Pyrightパターンに従う

### Research Needed（設計フェーズで調査）
- [ ] 大規模プロジェクト（1000ファイル超）でのパフォーマンス測定
- [ ] ファイルエンコーディング検出（Shift-JIS対応）
- [ ] メモリ使用量の確認

### テスト計画
- 既存テストリポジトリ（5ファイル）で基本動作確認
- 大規模テストリポジトリの作成検討
