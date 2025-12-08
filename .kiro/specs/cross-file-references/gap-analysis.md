# Gap Analysis: cross-file-references

## 現状調査

### 主要ファイルとモジュール構成

| ファイル | 役割 |
|---------|------|
| `server.py` | LSPサーバー本体、`find_references`ハンドラ |
| `index.py` | `SymbolIndex`クラス、シンボルと参照の管理 |
| `reference_tracker.py` | `ReferenceTracker`クラス、参照の抽出と検索 |
| `include_graph.py` | `IncludeGraph`クラス、Include依存関係の管理 |
| `reference.py` | `Reference`データクラス |

### 既存アーキテクチャパターン

1. **参照検索フロー**:
```
server.find_references()
  → self._index.find_references(word, include_declaration)
    → self._reference_tracker.find_references(name, include_declaration)
```

2. **インデックス更新フロー**:
```
server._open_document(uri, content)
  → self._update_index(uri, content)
    → self._index.update(uri, content, symbols)
      → self._reference_tracker.update(uri, content, symbols)
```

3. **ワークスペーススキャン**（workspace-initial-scanで実装済み）:
```
server._scan_workspace(root_path)
  → 全VBSファイルを走査
  → 各ファイルで server._open_document(uri, content) を呼び出し
```

### 既存の参照検索機能

`ReferenceTracker`は以下の機能を持つ:
- ドキュメントごとの参照をインデックス化
- 名前による参照検索（大文字小文字を区別しない）
- `include_declaration`オプションで定義箇所の包含/除外
- コメント・文字列リテラル内の参照を除外

## 要件実現可能性分析

### Requirement 1: 全インデックスファイルからの参照検索

**技術的ニーズ**:
- ワークスペーススキャンで登録されたファイルの参照を検索

**現状分析**:
- ✅ **既に実装済み**: `_scan_workspace`が全ファイルを`_open_document`経由で登録
- ✅ `ReferenceTracker`は`_references_by_name`辞書で全ドキュメントの参照を管理
- ✅ `find_references`は全インデックスを検索

**ギャップ**: なし（ワークスペーススキャン機能で対応済み）

**既存テスト**:
- `test_find_references_cross_document` - 複数ドキュメントからの参照検索

### Requirement 2: Include依存関係を考慮した参照検索

**技術的ニーズ**:
- Include経由で参照可能なファイルからの参照検索
- 循環Includeの安全な処理

**現状分析**:
- ✅ `IncludeGraph`は`get_transitive_includes()`と`get_includers()`を提供
- ✅ 循環参照検出は`has_cycle()`で実装済み
- ⚠️ **現在の`find_references`はInclude関係を考慮していない**

**ギャップ**: Include関係を考慮したスコープ制御が必要

**既存テスト**:
- `test_find_references_includes_references_from_includer_files`
- `test_find_references_searches_all_includers`
- これらのテストは`_open_document`で両ファイルを開いている前提

### Requirement 3: 参照結果の一貫性

**技術的ニーズ**:
- `include_declaration`フラグの正確な処理
- 重複除去

**現状分析**:
- ✅ `include_declaration`は`ReferenceTracker.find_references()`で処理済み
- ⚠️ 重複チェックは明示的に実装されていない

**ギャップ**: 重複除去の検証が必要（実装は存在する可能性あり）

### Requirement 4: パフォーマンス要件

**技術的ニーズ**:
- 1000ファイル規模で1秒以内の応答
- インデックス再構築なし

**現状分析**:
- ✅ `_references_by_name`辞書による O(1) ルックアップ
- ✅ インデックスは参照検索時に再構築されない
- ⚠️ 大規模プロジェクトでのベンチマーク未実施

**ギャップ**: パフォーマンステストの追加

### Requirement 5: エラーハンドリング

**技術的ニーズ**:
- 適切なエラー処理とログ出力

**現状分析**:
- ✅ `server.find_references()`は`content is None`の場合`None`を返却
- ✅ `word is None`の場合も`None`を返却
- ⚠️ 例外処理とログ出力の明示的な実装は限定的

**ギャップ**: エラーケースのテスト追加

## 実装アプローチオプション

### Option A: 既存コンポーネントの拡張

**対象ファイル**:
- `server.py` - `find_references`メソッドの拡張
- テストファイルの追加

**拡張内容**:
- Include関係を考慮した参照検索スコープの追加（オプション）
- エラーハンドリングの強化

**トレードオフ**:
- ✅ 最小限の変更で対応可能
- ✅ 既存のReferenceTracker/IncludeGraphを活用
- ❌ Include依存を考慮した場合、ロジックが複雑化する可能性

### Option B: 新規コンポーネントの作成

**該当なし**: 既存コンポーネントで十分対応可能

### Option C: ハイブリッドアプローチ

**推奨**: 段階的な実装

**フェーズ1**: 現状の動作確認と検証テスト追加
- ワークスペーススキャン後のクロスファイル参照検索が動作することを確認
- エラーハンドリングのテスト追加

**フェーズ2**: Include依存関係の考慮（オプション）
- `IncludeGraph`を活用した参照検索スコープの制御
- 必要に応じて実装

**トレードオフ**:
- ✅ 段階的に品質を向上
- ✅ リスクを分散
- ❌ 複数フェーズで作業量が増加

## 実装複雑度とリスク

### 工数見積もり: S (1-3日)

**理由**:
- 主要機能はworkspace-initial-scanで既に実装済み
- 既存パターンの活用で追加実装は最小限
- テスト追加が主な作業

### リスク: Low

**理由**:
- 既存の`ReferenceTracker`と`IncludeGraph`は成熟している
- テストカバレッジが既に高い
- アーキテクチャ変更なし

## 要件-資産マップ

| 要件 | 既存資産 | ギャップ |
|------|---------|---------|
| 1.1 全ファイル参照検索 | ReferenceTracker | なし（検証テスト追加） |
| 1.2 未オープンファイル対応 | _scan_workspace | なし（検証テスト追加） |
| 1.3 大文字小文字非区別 | ReferenceTracker | なし |
| 2.1 Include経由の参照 | IncludeGraph | スコープ制御（オプション） |
| 2.2 循環Include対応 | IncludeGraph.has_cycle() | なし |
| 3.1 include_declaration | ReferenceTracker | なし |
| 3.2 重複除去 | - | 検証必要 |
| 4.1 パフォーマンス | _references_by_name | ベンチマーク追加 |
| 5.1-5.3 エラーハンドリング | 部分実装 | テスト追加 |

## 設計フェーズへの推奨事項

### 推奨アプローチ
**Option C: ハイブリッドアプローチ**

### 主要な決定事項
1. Include依存関係を考慮した参照検索は必須か、オプションか
2. パフォーマンステストの具体的なベンチマーク基準

### 追加調査項目
- 現状の`find_references`がワークスペーススキャン後に正しく動作するかの実証テスト
- 大規模プロジェクト（100-1000ファイル）でのパフォーマンス計測
