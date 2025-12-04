# Implementation Plan

## Tasks

- [x] 1. README.mdにserena-vbs固有のヘッダーとフォーク説明を追加
  - プロジェクト冒頭にserena-vbsがSerenaのフォーク版であることを明記
  - VBScript/ASP言語サポートが追加機能であることを説明
  - オリジナルSerenaリポジトリへのリンクを追加
  - _Requirements: 1.4, 1.5_

- [x] 2. クイックスタートセクションを追加
- [x] 2.1 (P) uvxコマンドによるインストール・実行方法を記載
  - GitHub URL（`git+https://github.com/okurashoichi/serena-vbs`）を使用したuvxコマンド例
  - MCPサーバー起動コマンドの例
  - プロジェクトパスのプレースホルダー付き
  - _Requirements: 1.1_

- [x] 2.2 (P) Claude Code用のMCP設定例を追加
  - コピー可能な完全なJSONブロック
  - `mcpServers` セクションの設定形式
  - `/path/to/project` をユーザーが置き換える形式で記載
  - _Requirements: 1.2_

- [x] 2.3 (P) Claude Desktop用のMCP設定例を追加
  - コピー可能な完全なJSONブロック
  - 設定ファイルのパス情報
  - Claude Codeとの設定の違いがあれば明記
  - _Requirements: 1.3_

- [x] 3. 動作確認
  - uvxコマンドでのインストール・起動確認
  - README.mdのMarkdownレンダリング確認
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
