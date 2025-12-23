# Requirements Document

## Introduction

本ドキュメントは、SerenaのVBScript言語サーバーに`find_referencing_symbols`機能を追加するための要件を定義します。この機能は、LSP（Language Server Protocol）の「Find References」機能に対応し、指定されたシンボル（関数、変数、クラスなど）を参照している箇所をコードベース全体から検索します。

Serenaはシンボルレベルのコード理解と操作を提供するコーディングエージェントツールキットであり、本機能はコードリファクタリングや依存関係の分析において重要な役割を果たします。

## Requirements

### Requirement 1: シンボル参照の検索

**Objective:** As a 開発者, I want VBScriptコード内でシンボルが参照されている箇所を検索したい, so that リファクタリングや影響範囲の分析を効率的に行える

#### Acceptance Criteria
1. When ユーザーがシンボル名を指定して参照検索をリクエストした場合, the VBScript Language Server shall そのシンボルを参照しているすべての箇所を返却する
2. When 参照検索が実行された場合, the VBScript Language Server shall 各参照の位置情報（ファイルパス、行番号、列番号）を含む結果を返却する
3. If 指定されたシンボルがコードベース内に存在しない場合, then the VBScript Language Server shall 空の結果リストを返却する
4. The VBScript Language Server shall 関数呼び出し、変数参照、定数参照を含むすべての参照タイプを検索対象とする

### Requirement 2: 複数ファイルにまたがる参照検索

**Objective:** As a 開発者, I want プロジェクト内の複数のVBScriptファイルにまたがるシンボル参照を検索したい, so that 大規模なコードベースでも依存関係を把握できる

#### Acceptance Criteria
1. When 参照検索が実行された場合, the VBScript Language Server shall プロジェクト内のすべてのVBScript/ASPファイル（.vbs、.asp、.inc）を検索対象とする
2. When 複数ファイルに参照が存在する場合, the VBScript Language Server shall すべてのファイルからの参照結果を統合して返却する
3. The VBScript Language Server shall インクルードされたファイル（#include、SSI）内の参照も検索対象に含める

### Requirement 3: 参照コンテキストの提供

**Objective:** As a 開発者, I want 参照箇所のコンテキスト情報を取得したい, so that 参照の意味と使用方法を理解できる

#### Acceptance Criteria
1. When 参照検索結果を返却する場合, the VBScript Language Server shall 各参照を含むコード行の内容を提供する
2. When 参照検索結果を返却する場合, the VBScript Language Server shall 参照が含まれるシンボル（親関数やクラス）の情報を提供する
3. The VBScript Language Server shall 定義箇所と参照箇所を区別できるフラグを結果に含める

### Requirement 4: MCPツール統合

**Objective:** As a LLMクライアント, I want MCP経由でシンボル参照検索機能を利用したい, so that エージェントワークフローに統合できる

#### Acceptance Criteria
1. The Serena MCP Server shall `find_referencing_symbols`ツールをMCPクライアントに公開する
2. When `find_referencing_symbols`ツールが呼び出された場合, the Serena MCP Server shall シンボル名をパラメータとして受け取り、参照結果を返却する
3. The Serena MCP Server shall 既存のSerenaツールパターンに準拠した形式で結果を返却する
4. If 言語サーバーが未初期化の場合, then the Serena MCP Server shall 適切なエラーメッセージを返却する

### Requirement 5: パフォーマンスと信頼性

**Objective:** As a ユーザー, I want 参照検索が効率的に動作することを期待する, so that 大規模プロジェクトでもストレスなく利用できる

#### Acceptance Criteria
1. The VBScript Language Server shall シンボルインデックスを活用して効率的な参照検索を実行する
2. If 検索処理中にエラーが発生した場合, then the VBScript Language Server shall 部分的な結果とエラー情報を返却する
3. The VBScript Language Server shall 参照検索結果をログに記録し、デバッグを支援する
