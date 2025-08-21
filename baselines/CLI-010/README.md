# CLI-010: Interactive TUI Dashboard with Real-Time Updates - Baseline Implementation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

This baseline implementation provides a feature-rich Terminal User Interface (TUI) dashboard with real-time data updates, responsive layout, and interactive widgets. Built with Textual framework, it demonstrates modern TUI development patterns and best practices.

## Features Implemented

### Core Features (MUST)
- ✅ Multiple widgets with real-time data display
- ✅ Keyboard navigation between widgets
- ✅ Responsive layout for terminal resize
- ✅ Mouse interaction support
- ✅ Charts and graphs visualization
- ✅ Scrollable logs widget
- ✅ Theme customization

### Additional Features (SHOULD/MAY)
- ✅ Command palette with fuzzy search
- ✅ Data export functionality (JSON, CSV, YAML)
- ⚠️ Plugin system (partial - extension points defined)

## Dashboard Components

### Widgets
1. **Metrics Widget** - Real-time system metrics display
2. **Chart Widget** - Live performance charts with history
3. **System Monitor** - CPU, memory, disk, and network usage
4. **Data Table** - Sortable and filterable event data
5. **Logs Widget** - Scrollable log viewer with filtering
6. **Command Palette** - Quick command access with search
7. **Notifications** - User feedback and alerts

### Layout
- Responsive grid layout
- Automatic reflow on terminal resize
- Focus management and navigation
- Split pane support

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `F1` | Show help |
| `Ctrl+P` | Open command palette |
| `Ctrl+E` | Export data |
| `Ctrl+T` | Toggle theme |
| `Ctrl+L` | Clear logs |
| `Tab` | Focus next widget |
| `Shift+Tab` | Focus previous widget |
| `Arrow Keys` | Navigate within widgets |

## Mouse Support

- Click to focus widgets
- Scroll to navigate content
- Click and drag for selection
- Context menus on right-click

## Themes

Four built-in themes available:
- **Dark** (default) - Modern dark theme
- **Light** - Clean light theme
- **High Contrast** - Accessibility-focused
- **Solarized** - Popular color scheme

## Running the Dashboard

### Docker
```bash
docker build -t cli-010-dashboard .
docker run -it --rm cli-010-dashboard
```

### Local Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python -m src.main

# With custom config
python -m src.main --config config/dashboard.yaml --theme dark
```

## Configuration

The dashboard is highly configurable via YAML:

```yaml
# config/dashboard.yaml
title: "My Dashboard"
refresh_rate: 1.0
max_fps: 30

widgets:
  - type: metrics
    title: "System Metrics"
    position: {row: 0, col: 0}
    size: {width: 50, height: 10}

themes:
  - name: custom
    colors:
      background: "#1a1a1a"
      foreground: "#ffffff"
      primary: "#00ff00"
```

## Data Export

Export dashboard data in multiple formats:

```python
# Export formats supported
- JSON: Full structured data
- CSV: Flattened tabular data
- YAML: Human-readable format

# Export location
exports/dashboard_export_YYYYMMDD_HHMMSS.{format}
```

## Performance

- **Refresh Rate**: 30 FPS max
- **Update Latency**: < 50ms (P95)
- **Memory Usage**: < 256MB
- **CPU Usage**: < 10% idle, < 50% active

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Manual Testing
```bash
# Test responsive layout
python -m src.main
# Resize terminal window

# Test keyboard navigation
# Press Tab to cycle through widgets

# Test theme switching
# Press Ctrl+T to toggle themes
```

## Architecture

```
┌─────────────────────────────────────────┐
│            TUI Dashboard App            │
├─────────────────────────────────────────┤
│           Textual Framework             │
├──────────┬──────────┬──────────────────┤
│  Widgets │  Themes  │  Data Source     │
├──────────┼──────────┼──────────────────┤
│  Layout  │  Events  │  Export Manager  │
└──────────┴──────────┴──────────────────┘
```

## Extending the Dashboard

### Adding Custom Widgets

```python
from textual.widget import Widget

class CustomWidget(Widget):
    def render(self):
        return "Custom content"
    
    def on_mount(self):
        self.set_interval(1.0, self.update)
```

### Adding Custom Themes

```yaml
themes:
  - name: my_theme
    colors:
      background: "#000000"
      foreground: "#00ff00"
```

### Adding Data Sources

```python
class CustomDataSource(DataSource):
    async def get_metrics(self):
        return {"custom": "data"}
```

## Troubleshooting

### Terminal Compatibility
- Requires terminal with 256 color support
- Best experience with modern terminals (iTerm2, Windows Terminal, etc.)
- Fallback to basic colors on limited terminals

### Performance Issues
- Reduce refresh rate in config
- Disable animations
- Limit chart history points

### Display Issues
- Check TERM environment variable
- Ensure UTF-8 locale
- Verify terminal size (minimum 80x24)

## License

MIT

---

<a id="japanese"></a>
## 日本語

## 概要

このベースライン実装は、リアルタイムデータ更新、レスポンシブレイアウト、インタラクティブウィジェットを備えた機能豊富なターミナルユーザーインターフェース（TUI）ダッシュボードを提供します。Textualフレームワークで構築され、モダンなTUI開発パターンとベストプラクティスを示しています。

## 実装された機能

### コア機能 (MUST)
- ✅ リアルタイムデータ表示を持つ複数のウィジェット
- ✅ ウィジェット間のキーボードナビゲーション
- ✅ ターミナルリサイズ用のレスポンシブレイアウト
- ✅ マウスインタラクションサポート
- ✅ チャートとグラフの視覚化
- ✅ スクロール可能なログウィジェット
- ✅ テーマカスタマイゼーション

### 追加機能 (SHOULD/MAY)
- ✅ ファジー検索付きコマンドパレット
- ✅ データエクスポート機能（JSON、CSV、YAML）
- ⚠️ プラグインシステム（部分的 - 拡張ポイント定義済み）

## ダッシュボードコンポーネント

### ウィジェット
1. **メトリクスウィジェット** - リアルタイムシステムメトリクス表示
2. **チャートウィジェット** - 履歴付きライブパフォーマンスチャート
3. **システムモニター** - CPU、メモリ、ディスク、ネットワーク使用状況
4. **データテーブル** - ソート可能でフィルタ可能なイベントデータ
5. **ログウィジェット** - フィルタリング付きスクロール可能なログビューア
6. **コマンドパレット** - 検索付きクイックコマンドアクセス
7. **通知** - ユーザーフィードバックとアラート

### レイアウト
- レスポンシブグリッドレイアウト
- ターミナルリサイズ時の自動リフロー
- フォーカス管理とナビゲーション
- スプリットペインサポート

## キーボードショートカット

| キー | アクション |
|-----|--------|
| `q` | アプリケーション終了 |
| `F1` | ヘルプ表示 |
| `Ctrl+P` | コマンドパレットを開く |
| `Ctrl+E` | データエクスポート |
| `Ctrl+T` | テーマ切り替え |
| `Ctrl+L` | ログクリア |
| `Tab` | 次のウィジェットにフォーカス |
| `Shift+Tab` | 前のウィジェットにフォーカス |
| `矢印キー` | ウィジェット内でナビゲート |

## マウスサポート

- クリックでウィジェットにフォーカス
- スクロールでコンテンツをナビゲート
- クリック＆ドラッグで選択
- 右クリックでコンテキストメニュー

## テーマ

4つのビルトインテーマが利用可能：
- **Dark**（デフォルト） - モダンダークテーマ
- **Light** - クリーンライトテーマ
- **High Contrast** - アクセシビリティ重視
- **Solarized** - 人気のカラースキーム

## ダッシュボードの実行

### Docker
```bash
docker build -t cli-010-dashboard .
docker run -it --rm cli-010-dashboard
```

### ローカルインストール
```bash
# 依存関係のインストール
pip install -r requirements.txt

# ダッシュボードの実行
python -m src.main

# カスタム設定で実行
python -m src.main --config config/dashboard.yaml --theme dark
```

## 設定

ダッシュボードはYAMLで高度に設定可能：

```yaml
# config/dashboard.yaml
title: "My Dashboard"
refresh_rate: 1.0
max_fps: 30

widgets:
  - type: metrics
    title: "システムメトリクス"
    position: {row: 0, col: 0}
    size: {width: 50, height: 10}

themes:
  - name: custom
    colors:
      background: "#1a1a1a"
      foreground: "#ffffff"
      primary: "#00ff00"
```

## データエクスポート

ダッシュボードデータを複数の形式でエクスポート：

```python
# サポートされるエクスポート形式
- JSON: 完全な構造化データ
- CSV: フラット化された表形式データ
- YAML: 人間が読める形式

# エクスポート場所
exports/dashboard_export_YYYYMMDD_HHMMSS.{format}
```

## パフォーマンス

- **リフレッシュレート**: 最大30 FPS
- **更新レイテンシ**: < 50ms (P95)
- **メモリ使用量**: < 256MB
- **CPU使用率**: < 10% アイドル、< 50% アクティブ

## テスト

### ユニットテスト
```bash
pytest tests/unit/ -v
```

### 統合テスト
```bash
pytest tests/integration/ -v
```

### 手動テスト
```bash
# レスポンシブレイアウトをテスト
python -m src.main
# ターミナルウィンドウをリサイズ

# キーボードナビゲーションをテスト
# Tabを押してウィジェット間を移動

# テーマ切り替えをテスト
# Ctrl+Tを押してテーマを切り替え
```

## アーキテクチャ

```
┌─────────────────────────────────────────┐
│            TUIダッシュボードアプリ           │
├─────────────────────────────────────────┤
│           Textualフレームワーク           │
├──────────┬──────────┬──────────────────┤
│ ウィジェット │  テーマ  │  データソース     │
├──────────┼──────────┼──────────────────┤
│ レイアウト │ イベント  │ エクスポートマネージャ │
└──────────┴──────────┴──────────────────┘
```

## ダッシュボードの拡張

### カスタムウィジェットの追加

```python
from textual.widget import Widget

class CustomWidget(Widget):
    def render(self):
        return "カスタムコンテンツ"
    
    def on_mount(self):
        self.set_interval(1.0, self.update)
```

### カスタムテーマの追加

```yaml
themes:
  - name: my_theme
    colors:
      background: "#000000"
      foreground: "#00ff00"
```

### データソースの追加

```python
class CustomDataSource(DataSource):
    async def get_metrics(self):
        return {"custom": "data"}
```

## トラブルシューティング

### ターミナル互換性
- 256色サポートのターミナルが必要
- モダンターミナル（iTerm2、Windows Terminal等）で最高の体験
- 制限されたターミナルでは基本色にフォールバック

### パフォーマンス問題
- 設定でリフレッシュレートを削減
- アニメーションを無効化
- チャート履歴ポイントを制限

### 表示問題
- TERM環境変数を確認
- UTF-8ロケールを確認
- ターミナルサイズを検証（最小80x24）

## ライセンス

MIT