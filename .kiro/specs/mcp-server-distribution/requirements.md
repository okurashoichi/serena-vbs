# Requirements Document

## Introduction
serena-vbs（VBScript/ASP対応を追加したSerena MCPサーバーのフォーク版）を、ユーザーが簡単にインストール・利用できるようにする。`uvx` コマンドによるGitHubからの直接実行が可能なため、READMEにインストール手順と設定例を追加することで配布を簡素化する。

## Requirements

### Requirement 1: READMEにクイックスタートを追加
**Objective:** As a ユーザー, I want インストール・設定手順をコピペできる, so that 迷わずセットアップできる

#### Acceptance Criteria
1. The README shall `uvx` コマンドによるインストール・実行方法を含む
2. The README shall Claude Code用のMCP設定例（JSON）を含む
3. The README shall Claude Desktop用のMCP設定例（JSON）を含む
4. The README shall VBScript/ASP対応に関する説明を含む
5. While オリジナルSerenaのドキュメントを参照する場合, the README shall このフォーク版の差分について明記する
