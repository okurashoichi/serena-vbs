# Requirements Document

## Introduction

VBScript/ASP のインクルードファイル間の参照追跡機能を実装する。Classic ASP では `<!--#include file="..." -->` や `<!--#include virtual="..." -->` ディレクティブを使用してファイル間でコードを共有するが、現在の VBScript LSP はこれらのインクルード関係を解析せず、ファイル間のシンボル参照を追跡できない。本機能により、インクルードされたファイル内のシンボル定義への Go to Definition や、インクルード元からのシンボル参照を Find References で検出可能とする。

## Requirements

### Requirement 1: インクルードディレクティブの解析

**Objective:** As a 開発者, I want インクルードディレクティブを自動的に解析してファイル間の依存関係を把握したい, so that インクルードされたファイルのシンボルを参照元から認識できる

#### Acceptance Criteria
1. When ASPファイルに `<!--#include file="path/to/file.asp" -->` ディレクティブが含まれる, the VBScript Language Server shall ディレクティブを検出し、対象ファイルのパスを抽出する
2. When ASPファイルに `<!--#include virtual="/path/to/file.asp" -->` ディレクティブが含まれる, the VBScript Language Server shall 仮想パスを解決して対象ファイルのパスを抽出する
3. When インクルードディレクティブ内のパスが相対パスである, the VBScript Language Server shall 参照元ファイルのディレクトリを基準に絶対パスを解決する
4. The VBScript Language Server shall インクルードディレクティブの行番号と文字位置を記録する

### Requirement 2: インクルードファイルグラフの構築

**Objective:** As a 開発者, I want ファイル間のインクルード関係をグラフとして把握したい, so that 循環参照や依存関係の問題を検出できる

#### Acceptance Criteria
1. When 複数のASPファイルがワークスペースに存在する, the VBScript Language Server shall 全ファイルのインクルード関係を有向グラフとして構築する
2. When ファイルAがファイルBをインクルードし、ファイルBがファイルCをインクルードする, the VBScript Language Server shall 推移的なインクルード関係を追跡する
3. If ファイル間に循環インクルードが検出される, the VBScript Language Server shall 警告としてログ出力し、無限ループを防止する
4. When ドキュメントが変更される, the VBScript Language Server shall 該当ファイルのインクルード関係のみを再計算する

### Requirement 3: インクルードファイル間のシンボル定義検索

**Objective:** As a 開発者, I want インクルードされたファイルで定義されたシンボルの定義元へジャンプしたい, so that コードベース全体を効率的にナビゲートできる

#### Acceptance Criteria
1. When 参照元ファイルでインクルードファイル内のシンボル名を Go to Definition する, the VBScript Language Server shall インクルードファイル内の定義位置を返す
2. When 同名シンボルが複数のインクルードファイルに存在する, the VBScript Language Server shall 全ての定義位置をリストとして返す
3. When ネストしたインクルード（A→B→C）の関係がある, the VBScript Language Server shall 最深部のファイルCで定義されたシンボルも参照元Aから検索可能とする
4. While インクルードファイルがワークスペース外に存在する, the VBScript Language Server shall 該当シンボルの定義検索結果を空として返す

### Requirement 4: インクルードファイル間のシンボル参照検索

**Objective:** As a 開発者, I want シンボルがどのファイルから参照されているかを把握したい, so that シンボルの変更影響範囲を正確に理解できる

#### Acceptance Criteria
1. When インクルードファイル内のシンボルを Find References する, the VBScript Language Server shall インクルード元ファイル内の参照位置を全て返す
2. When シンボルがインクルード元とインクルード先の両方で使用される, the VBScript Language Server shall 両方のファイルからの参照を統合して返す
3. When シンボルの参照検索で include_declaration=true を指定する, the VBScript Language Server shall 定義位置も結果に含める
4. The VBScript Language Server shall 参照検索結果にファイルURIと行・列位置を含める

### Requirement 5: インクルードディレクティブのシンボル情報提供

**Objective:** As a 開発者, I want インクルードディレクティブ自体もシンボルとして認識したい, so that インクルード関係を Document Symbols で確認できる

#### Acceptance Criteria
1. When Document Symbols をリクエストする, the VBScript Language Server shall インクルードディレクティブを SymbolKind.File としてシンボル一覧に含める
2. The VBScript Language Server shall インクルードシンボルの名前にインクルード先ファイルパスを設定する
3. When インクルードディレクティブのパスが解決不能である, the VBScript Language Server shall シンボル名にエラーマーカーを付与する

### Requirement 6: ワークスペース変更時のインクルードグラフ更新

**Objective:** As a 開発者, I want ファイルの追加・削除・変更時にインクルード関係が自動更新されてほしい, so that 常に最新の依存関係に基づいた解析が行われる

#### Acceptance Criteria
1. When 新規ファイルがワークスペースに追加される, the VBScript Language Server shall 既存ファイルからのインクルード参照を再評価する
2. When ファイルがワークスペースから削除される, the VBScript Language Server shall 該当ファイルへのインクルード参照を無効としてマークする
3. When ファイル内のインクルードディレクティブが変更される, the VBScript Language Server shall インクルードグラフの該当エッジのみを更新する
4. The VBScript Language Server shall グラフ更新時に影響を受けるファイルのシンボルインデックスを再構築する
