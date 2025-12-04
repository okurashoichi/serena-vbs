# Design Document: MCP Server Distribution

## Overview

**Purpose**: serena-vbs（VBScript/ASP対応を追加したSerena MCPサーバーのフォーク版）を、ユーザーが簡単にインストール・利用できるようにする。

**Users**: VBScript/ASPプロジェクトで作業する開発者がClaude Code/Desktopと連携して利用する。

**Impact**: 既存のREADME.mdにクイックスタートセクションを追加する。

### Goals
- ユーザーがコピペで設定を完了できる
- Claude Code/Desktop両方の設定例を提供
- VBScript/ASP対応の差分を明確化

### Non-Goals
- PyPI公開（現時点では不要）
- 新規CLIコマンドの追加
- 自動設定ツールの開発

## Architecture

### Existing Architecture Analysis

現在のREADME.mdはオリジナルSerenaのものを継承しており、以下の変更が必要：

- クイックスタートセクションの追加（serena-vbs固有のGitHub URL）
- VBScript/ASP対応に関する説明の追加
- オリジナルSerenaとの差分の明記

### Technology Stack

| Layer | Choice / Version | Role in Feature | Notes |
|-------|------------------|-----------------|-------|
| Documentation | Markdown | README.md更新 | 既存形式を維持 |
| Distribution | uvx + GitHub | パッケージ配布 | PyPI不要 |

## Requirements Traceability

| Requirement | Summary | Components | Interfaces | Flows |
|-------------|---------|------------|------------|-------|
| 1.1 | uvxコマンドによるインストール方法 | README Quick Start | N/A | N/A |
| 1.2 | Claude Code用設定例 | README Quick Start | JSON設定 | N/A |
| 1.3 | Claude Desktop用設定例 | README Quick Start | JSON設定 | N/A |
| 1.4 | VBScript/ASP対応説明 | README Features | N/A | N/A |
| 1.5 | オリジナルSerenaとの差分 | README Header | N/A | N/A |

## Components and Interfaces

| Component | Domain/Layer | Intent | Req Coverage | Key Dependencies | Contracts |
|-----------|--------------|--------|--------------|------------------|-----------|
| README Quick Start | Documentation | インストール・設定手順の提供 | 1.1, 1.2, 1.3 | N/A | N/A |
| README Features | Documentation | VBScript/ASP対応の説明 | 1.4, 1.5 | N/A | N/A |

### Documentation

#### README Quick Start Section

| Field | Detail |
|-------|--------|
| Intent | uvxコマンドとMCPクライアント設定例を提供 |
| Requirements | 1.1, 1.2, 1.3 |

**Responsibilities & Constraints**
- GitHubリポジトリURLを使用したuvxコマンド例
- Claude Code用のJSON設定例
- Claude Desktop用のJSON設定例
- プロジェクトパスのプレースホルダー付き

**Implementation Notes**
- 設定例はコピー可能な完全なJSONブロックとして提供
- `/path/to/project` をユーザーが置き換える形式

#### README VBScript/ASP Section

| Field | Detail |
|-------|--------|
| Intent | VBScript/ASP言語サポートの説明 |
| Requirements | 1.4, 1.5 |

**Responsibilities & Constraints**
- オリジナルSerenaとの関係を明記
- VBScript/ASP対応が追加機能であることを説明
- オリジナルのドキュメントへのリンク

## Testing Strategy

### Manual Testing
- uvxコマンドでのインストール確認
- Claude Code設定例の動作確認
- README.mdのMarkdownレンダリング確認
