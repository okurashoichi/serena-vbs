# Implementation Plan

## Task 1: VBScriptパーサーコア実装
- [x] 1. VBScriptパーサーコア実装

- [x] 1.1 (P) VBScript構文解析の基盤を構築する
  - VBScriptの基本シンボル（Function、Sub）を正規表現で検出する機能を実装する
  - 大文字小文字を区別しない（case-insensitive）パターンマッチングを行う
  - 検出されたシンボルの名前、種別、位置情報（行番号・カラム）を抽出する
  - Public/Private修飾子の有無を認識する
  - シンボル情報をLSP DocumentSymbol形式に変換するロジックを実装する
  - _Requirements: 2.3_

- [x] 1.2 (P) Class定義とProperty定義の解析機能を追加する
  - Class定義（Class...End Class）を検出し、階層構造を持つシンボルとして抽出する
  - Property Get/Let/Setを検出し、適切なSymbolKindで表現する
  - クラス内のメンバー（Function、Sub、Property）を子要素として再帰的に抽出する
  - End Class/End Property/End Function等の終端パターンを正確に検出する
  - _Requirements: 2.3_

## Task 2: ASPファイル対応
- [x] 2. ASPファイル対応

- [x] 2.1 ASPファイルからVBScriptブロックを抽出する機能を実装する
  - `<% ... %>` デリミタで囲まれたサーバーサイドスクリプトブロックを検出する
  - `<script runat="server">...</script>` 形式のブロックを検出する
  - 出力式 `<%= ... %>` はシンボル抽出対象外として識別する
  - 各ブロックの開始位置（行番号・カラム）を正確に算出する
  - 抽出されたブロックの位置情報を保持し、パーサーに渡せる形式で返す
  - _Requirements: 4.2_

- [x] 2.2 ASPブロック内のシンボル位置を元ファイルの位置に変換する
  - パーサーが返すシンボル位置にブロックのオフセットを加算する
  - 複数のVBScriptブロックを持つASPファイルで正しい位置を返せるようにする
  - HTMLとVBScriptが混在するファイルでシンボル一覧が正しく取得できることを確認する
  - _Requirements: 4.2_

## Task 3: シンボルインデックス実装
- [x] 3. シンボルインデックス実装

- [x] 3.1 ワークスペース全体のシンボル情報を管理する仕組みを構築する
  - ドキュメントごとにシンボル情報を保持するデータ構造を実装する
  - シンボル名による高速検索を可能にするインデックスを構築する
  - ドキュメントが変更された際にインデックスを更新する機能を実装する
  - ドキュメントがクローズされた際にインデックスから削除する機能を実装する
  - _Requirements: 2.4, 2.5_

- [x] 3.2 定義検索と参照検索のクエリ機能を実装する
  - シンボル名から定義位置（Location）を返す検索機能を実装する
  - シンボル名からすべての参照位置を返す検索機能を実装する
  - 検索時に大文字小文字を区別しないマッチングを行う
  - 宣言自体を参照に含めるかどうかのオプションを提供する
  - _Requirements: 2.4, 2.5_

## Task 4: pygls LSPサーバー実装
- [x] 4. pygls LSPサーバー実装

- [x] 4.1 pyglsを使用したLSPサーバーの基盤を構築する
  - pygls LanguageServerインスタンスを作成し、サーバー名とバージョンを設定する
  - STDIOモードでの通信を可能にするエントリーポイントを実装する
  - textDocument/didOpenイベントでドキュメントをパースしインデックスを更新する
  - textDocument/didChangeイベントで変更されたドキュメントを再パースする
  - textDocument/didCloseイベントでインデックスからドキュメントを削除する
  - _Requirements: 2.2, 2.3_

- [x] 4.2 LSPプロトコルのシンボル関連メソッドを実装する
  - textDocument/documentSymbolリクエストに対してドキュメント内のシンボル一覧を返す
  - textDocument/definitionリクエストに対してカーソル位置の単語から定義位置を返す
  - textDocument/referencesリクエストに対してシンボルの参照位置一覧を返す
  - カーソル位置から単語を抽出するユーティリティ機能を実装する
  - _Requirements: 2.3, 2.4, 2.5_

## Task 5: Serena統合レイヤー実装
- [x] 5. Serena統合レイヤー実装

- [x] 5.1 VBScript用のLanguage enum設定を追加する
  - Language enumにVBSCRIPTエントリを追加する
  - .vbs、.asp、.incファイル拡張子を認識するFilenameMatcher設定を追加する
  - VBScriptLanguageServerクラスを返すget_ls_class()マッピングを追加する
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 5.2 pygls LSPプロセスを起動・管理するラッパークラスを実装する
  - SolidLanguageServerを継承したVBScriptLanguageServerクラスを作成する
  - pyglsサーバーを子プロセスとしてSTDIOモードで起動する機能を実装する
  - LSP initializeリクエストを送信しサーバーの初期化を完了する
  - プロセス終了時のクリーンアップ処理を実装する
  - _Requirements: 2.1, 2.2_

- [x] 5.3 VBScript固有の設定とエラーハンドリングを実装する
  - bin、obj、Backupなどの一般的な非ソースディレクトリを除外する設定を追加する
  - ファイルエンコーディング（UTF-8、Shift_JIS等）を設定可能にする
  - pygls/lsprotocolが見つからない場合のエラーメッセージとインストール手順を表示する
  - .serena/設定ファイルからプロジェクト固有の設定を読み込む機能を実装する
  - _Requirements: 2.6, 4.1, 4.3, 4.4_

## Task 6: 依存関係とプロジェクト設定
- [x] 6. 依存関係とプロジェクト設定

- [x] 6.1 pyglsとlsprotocolの依存関係を追加する
  - pyproject.tomlにpygls (^2.0.0) とlsprotocol依存関係を追加する
  - 依存関係がインストールされているかを確認するチェック機能を実装する
  - Linux、macOS、Windowsの各プラットフォームで動作することを確認する
  - _Requirements: 3.1, 3.2, 3.5_

- [x] 6.2 依存関係の自動セットアップ機能を実装する
  - 初回使用時に依存関係の存在を確認する
  - 不足している場合はuvまたはpipを使用した自動インストールを試みる
  - インストール中の進捗情報をユーザーに表示する
  - _Requirements: 3.3, 3.4_

## Task 7: テスト環境構築
- [x] 7. テスト環境構築

- [x] 7.1 テストリポジトリとテストケースを準備する
  - test/resources/repos/vbscript/test_repo/に代表的なVBScriptコードを配置する
  - 基本的なFunction/Subを含むテストファイルを作成する
  - Class定義を含むテストファイルを作成する
  - Property Get/Let/Setを含むテストファイルを作成する
  - ASP埋め込みVBScriptのテストファイルを作成する
  - インクルードファイル（.inc）のテストケースを作成する
  - _Requirements: 5.1_

- [x] 7.2 (P) pytest vbscriptマーカーを登録する
  - pyproject.tomlにvbscriptマーカーを追加する
  - VBScript関連テストにマーカーを適用する
  - _Requirements: 5.4_

## Task 8: 単体テスト実装
- [x] 8. 単体テスト実装

- [x] 8.1 (P) VBScriptパーサーの単体テストを作成する
  - Function抽出のテストケースを作成する
  - Sub抽出のテストケースを作成する
  - Class抽出のテストケースを作成する
  - Property抽出のテストケースを作成する
  - 大文字小文字混在のテストケースを作成する
  - 不正な構文での堅牢性テストを作成する
  - _Requirements: 5.2_

- [x] 8.2 (P) ASPスクリプト抽出機能の単体テストを作成する
  - <% %>ブロック抽出のテストケースを作成する
  - <script runat="server">ブロック抽出のテストケースを作成する
  - 複数ブロック混在時のテストケースを作成する
  - 位置オフセット計算の正確性テストを作成する
  - _Requirements: 5.2_

- [x] 8.3 (P) シンボルインデックスの単体テストを作成する
  - インデックス更新のテストケースを作成する
  - 定義検索のテストケースを作成する
  - 参照検索のテストケースを作成する
  - ドキュメント削除時のインデックス更新テストを作成する
  - _Requirements: 5.2_

## Task 9: 統合テスト実装
- [x] 9. 統合テスト実装

- [x] 9.1 LSPサーバーの統合テストを作成する
  - LSPサーバー起動・初期化の統合テストを作成する
  - textDocument/documentSymbolのエンドツーエンドテストを作成する
  - textDocument/definitionのエンドツーエンドテストを作成する
  - textDocument/referencesのエンドツーエンドテストを作成する
  - _Requirements: 5.2_

- [x] 9.2 Serena統合の動作確認テストを作成する
  - VBScriptプロジェクトの自動検出テストを作成する
  - .vbs/.asp/.incファイルの認識テストを作成する
  - MCP経由でのシンボル検索テストを作成する
  - エラーハンドリングのテストを作成する
  - _Requirements: 5.2_

## Requirements Coverage

| Requirement | Tasks |
|-------------|-------|
| 1.1 | 5.1 |
| 1.2 | 5.1 |
| 1.3 | 5.1 |
| 1.4 | 5.1 |
| 2.1 | 5.2 |
| 2.2 | 4.1, 5.2 |
| 2.3 | 1.1, 1.2, 4.1, 4.2 |
| 2.4 | 3.1, 3.2, 4.2 |
| 2.5 | 3.1, 3.2, 4.2 |
| 2.6 | 5.3 |
| 3.1 | 6.1 |
| 3.2 | 6.1 |
| 3.3 | 6.2 |
| 3.4 | 6.2 |
| 3.5 | 6.1 |
| 4.1 | 5.3 |
| 4.2 | 2.1, 2.2 |
| 4.3 | 5.3 |
| 4.4 | 5.3 |
| 5.1 | 7.1 |
| 5.2 | 8.1, 8.2, 8.3, 9.1, 9.2 |
| 5.4 | 7.2 |
