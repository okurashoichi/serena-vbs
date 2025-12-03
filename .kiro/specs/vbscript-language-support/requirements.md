# Requirements Document

## Introduction

本ドキュメントでは、SerenaにVBScript言語サポートを追加するための要件を定義する。VBScriptは主にClassic ASP（Active Server Pages）やWindowsスクリプティングで使用されるレガシー言語であり、LSP（Language Server Protocol）を通じてセマンティックなコード解析・編集機能を提供することで、レガシーコードベースの保守・移行作業を支援する。

## Requirements

### Requirement 1: 言語サーバー設定の追加
**Objective:** As a 開発者, I want SerenaでVBScriptファイルを認識できるようにしたい, so that VBScriptプロジェクトでSerenaのセマンティック機能を利用できる

#### Acceptance Criteria
1. The Serena system shall recognize files with `.vbs`, `.asp`, and `.inc` extensions as VBScript source files
2. When a VBScript project is opened, the Serena system shall automatically detect VBScript as the primary language
3. The Serena system shall register `VBSCRIPT` as a valid entry in the Language enumeration
4. When the language is set to `vbscript`, the Serena system shall instantiate the appropriate VBScript language server class

### Requirement 2: 言語サーバー実装
**Objective:** As a 開発者, I want VBScript用のLSPラッパーを使いたい, so that シンボル検索や参照検索などのIDE機能を利用できる

#### Acceptance Criteria
1. The VBScript language server shall extend `SolidLanguageServer` base class following the established pattern
2. When the language server is started, the Serena system shall launch the external VBScript LSP process
3. The VBScript language server shall support the `textDocument/documentSymbol` LSP method for symbol extraction
4. The VBScript language server shall support the `textDocument/definition` LSP method for go-to-definition functionality
5. The VBScript language server shall support the `textDocument/references` LSP method for find-references functionality
6. If the external VBScript LSP is not installed, the Serena system shall display a clear error message with installation instructions

### Requirement 3: ランタイム依存関係の管理
**Objective:** As a ユーザー, I want VBScript LSPが自動的にセットアップされてほしい, so that 手動でのインストール手順を最小限にできる

#### Acceptance Criteria
1. The Serena system shall define runtime dependencies for the VBScript language server
2. When the VBScript language server is first used, the Serena system shall check for required dependencies
3. If dependencies are missing, the Serena system shall attempt automatic installation using appropriate package manager
4. While dependencies are being installed, the Serena system shall display progress information to the user
5. The Serena system shall support installation on Linux, macOS, and Windows platforms

### Requirement 4: VBScript固有の設定
**Objective:** As a 開発者, I want VBScript特有のファイルパターンや除外ディレクトリを設定したい, so that プロジェクト構造に適した解析ができる

#### Acceptance Criteria
1. The VBScript language server shall ignore common non-source directories (e.g., `bin`, `obj`, `Backup`)
2. When Classic ASP files are detected, the Serena system shall handle embedded VBScript within HTML context
3. The VBScript language server shall support configurable file encoding (e.g., Shift_JIS, UTF-8) for legacy codebases
4. Where project-specific settings are provided in `.serena/` configuration, the Serena system shall apply those settings

### Requirement 5: テストとドキュメント
**Objective:** As a コントリビューター, I want VBScriptサポートがテスト可能であってほしい, so that 品質を維持しながら開発を続けられる

#### Acceptance Criteria
1. The Serena system shall include a test repository under `test/resources/repos/vbscript/` with representative VBScript code
2. When running tests with the `vbscript` marker, the Serena system shall execute VBScript-specific test cases
3. The VBScript language support shall be documented in the project's language support documentation
4. The Serena system shall register a pytest marker `vbscript` for conditional test execution
