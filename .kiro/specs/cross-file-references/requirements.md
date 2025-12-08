# Requirements Document

## Introduction

VBScript LSPのワークスペース初期スキャン機能（workspace-initial-scan）によって、サーバー起動時に全VBScriptファイルがインデックス化されるようになった。本機能では、このインデックスを活用して`textDocument/references`がプロジェクト全体から参照を返すように強化する。

現在の実装では、ワークスペーススキャン時に全ファイルの参照情報が`ReferenceTracker`に登録されるため、基本的なクロスファイル参照検索は可能である。しかし、以下の課題が存在する：
- Include依存関係を考慮した参照検索のスコープ制御
- 大規模プロジェクトでのパフォーマンス最適化
- 参照結果の整合性検証

## Requirements

### Requirement 1: 全インデックスファイルからの参照検索

**Objective:** As a 開発者, I want 未オープンのファイルからも参照を検索できること, so that プロジェクト全体の依存関係を把握できる

#### Acceptance Criteria
1. When textDocument/referencesリクエストを受信した場合, the VBScript LSP shall 全インデックス済みファイルから該当シンボルの参照を返却する
2. When シンボルがファイルAで定義されファイルBで使用されている場合, the VBScript LSP shall ファイルBを開かなくても参照を検索結果に含める
3. The VBScript LSP shall 大文字小文字を区別せずに参照を検索する（VBScriptの仕様に準拠）
4. If 検索対象シンボルが見つからない場合, then the VBScript LSP shall 空のリストを返却する

### Requirement 2: Include依存関係を考慮した参照検索

**Objective:** As a 開発者, I want Include経由で参照されているシンボルも検索対象に含めたい, so that ASPプロジェクトの依存関係を正確に把握できる

#### Acceptance Criteria
1. When textDocument/referencesリクエストを受信した場合, the VBScript LSP shall Include経由で参照可能なファイルからも参照を検索する
2. When ファイルAがファイルBをIncludeしている場合, the VBScript LSP shall ファイルBで定義されたシンボルへの参照をファイルAからも検索する
3. The VBScript LSP shall 循環Includeが存在する場合でも無限ループせずに参照を検索する

### Requirement 3: 参照結果の一貫性

**Objective:** As a 開発者, I want 参照検索結果が一貫していること, so that リファクタリング時に信頼できる結果を得られる

#### Acceptance Criteria
1. When include_declarationがtrueの場合, the VBScript LSP shall 定義箇所を参照結果に含める
2. When include_declarationがfalseの場合, the VBScript LSP shall 定義箇所を参照結果から除外する
3. The VBScript LSP shall 同一ファイル内の参照と他ファイルの参照を区別せず統一的に返却する
4. The VBScript LSP shall 参照結果を重複なく返却する

### Requirement 4: パフォーマンス要件

**Objective:** As a 開発者, I want 参照検索が高速に完了すること, so that 開発ワークフローが中断されない

#### Acceptance Criteria
1. While インデックスに1000ファイルが登録されている場合, the VBScript LSP shall 参照検索を1秒以内に完了する
2. The VBScript LSP shall 参照検索時にインデックスの再構築を行わない（既存インデックスを利用）
3. The VBScript LSP shall メモリ効率的に参照情報を管理する

### Requirement 5: エラーハンドリング

**Objective:** As a 開発者, I want エラー時でも適切なレスポンスを受け取りたい, so that デバッグが容易になる

#### Acceptance Criteria
1. If カーソル位置にシンボルが存在しない場合, then the VBScript LSP shall nullを返却する
2. If 対象ドキュメントがインデックスに存在しない場合, then the VBScript LSP shall nullを返却する
3. If 内部エラーが発生した場合, then the VBScript LSP shall 例外を適切に処理しログを出力する
