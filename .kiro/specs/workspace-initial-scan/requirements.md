# Requirements Document

## Introduction

VBScript LSPのワークスペース初期スキャン機能を実装する。現状のVBScript LSPは「開いたファイルのみ」をインデックス対象としているため、未オープンファイルのシンボル検索ができない。本機能により、サーバー起動時にワークスペース内の全VBScript関連ファイル（.vbs, .asp, .inc）を自動スキャンし、SymbolIndexに登録することで、プロジェクト全体のシンボル検索を可能にする。

**現状の問題**:
- ファイルを明示的に開かないとインデックスに追加されない
- クロスファイルの定義ジャンプや参照検索が機能しない
- 他の言語（Python/TypeScript等）と比較して機能が劣る

**目標**:
- サーバー起動時に全対象ファイルを自動スキャン
- 未オープンファイルのシンボルも検索可能に
- Pyrightなど他の言語サーバーと同等の機能レベルを実現

## Requirements

### Requirement 1: ワークスペーススキャン対象ファイルの特定

**Objective:** As a VBScript LSP利用者, I want サーバーがVBScript関連ファイルを自動的に特定してくれること, so that 手動でファイルを開く必要がなくなる

#### Acceptance Criteria
1. When VBScript LSPサーバーが起動した時, the VBScript LSP shall ワークスペースルートから再帰的にファイルを探索する
2. The VBScript LSP shall 拡張子 `.vbs`, `.VBS`, `.asp`, `.ASP`, `.inc`, `.INC` のファイルをスキャン対象として認識する
3. While ディレクトリを探索中, the VBScript LSP shall `.git`, `node_modules`, `Backup`, `bin`, `obj` ディレクトリを除外する
4. While ディレクトリを探索中, the VBScript LSP shall ドットで始まるディレクトリ（隠しディレクトリ）を除外する

### Requirement 2: ファイルのパースとインデックス登録

**Objective:** As a VBScript LSP利用者, I want スキャンしたファイルのシンボルがインデックスに登録されること, so that 後でシンボル検索ができる

#### Acceptance Criteria
1. When 対象ファイルが検出された時, the VBScript LSP shall ファイル内容を読み込みパースを実行する
2. When ファイルのパースが成功した時, the VBScript LSP shall 検出されたシンボル（Function, Sub, Class, Property等）をSymbolIndexに登録する
3. If ファイルのパースに失敗した場合, the VBScript LSP shall エラーをログに記録し次のファイルの処理を継続する
4. If ファイルの読み込みに失敗した場合（権限エラー等）, the VBScript LSP shall 警告をログに記録し次のファイルの処理を継続する

### Requirement 3: スキャン完了通知とログ出力

**Objective:** As a 開発者, I want スキャン進捗と完了を確認できること, so that サーバーの状態を把握できる

#### Acceptance Criteria
1. When ワークスペーススキャンが完了した時, the VBScript LSP shall `Found N source files` 形式でログを出力する（Nはスキャンしたファイル数）
2. When ワークスペーススキャンが完了した時, the VBScript LSP shall 内部の完了フラグ（analysis_complete等）をセットする
3. The VBScript LSP shall スキャン中にDEBUGレベルで個別ファイルの処理状況をログ出力する

### Requirement 4: 既存機能との統合

**Objective:** As a VBScript LSP利用者, I want 初期スキャンされたシンボルで既存のLSP機能が動作すること, so that プロジェクト全体でシンボル検索ができる

#### Acceptance Criteria
1. When `textDocument/definition`リクエストを受信した時 and 対象シンボルが初期スキャンでインデックス済みの場合, the VBScript LSP shall そのシンボルの定義位置を返す
2. When `textDocument/references`リクエストを受信した時, the VBScript LSP shall 初期スキャンでインデックスされた全ファイルから参照を検索する
3. When 新たにファイルがオープンされた時 and そのファイルが既にインデックス済みの場合, the VBScript LSP shall インデックスを最新の内容で更新する

### Requirement 5: パフォーマンス要件

**Objective:** As a VBScript LSP利用者, I want サーバー起動が実用的な時間で完了すること, so that 開発作業に支障がない

#### Acceptance Criteria
1. The VBScript LSP shall 100ファイル規模のプロジェクトを5秒以内にスキャン完了する
2. The VBScript LSP shall スキャン処理をブロッキングで実行し、完了後にLSPリクエストの受付を開始する
3. If ファイル数が1000を超える場合, the VBScript LSP shall 警告ログを出力する（大規模プロジェクトの認識用）
