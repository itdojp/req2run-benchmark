# Req2Run Environment Setup Guide

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

### Quick Start

The fastest way to get started with Req2Run benchmark development:

```bash
# Clone the repository
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark

# Run the automated setup script
# For Linux/Mac:
./scripts/setup-env.sh

# For Windows PowerShell:
.\scripts\setup-env.ps1

# For Windows CMD:
scripts\setup-env.bat
```

### Manual Setup Options

#### Option 1: Python Virtual Environment (Recommended)

##### Linux/Mac
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

##### Windows
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# Or for CMD
venv\Scripts\activate.bat

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### Option 2: Docker Environment (Most Reliable)

```bash
# Build the Docker image
docker build -t req2run-env .

# Run with volume mount for development
docker run -it -v $(pwd):/workspace req2run-env bash

# Or use docker-compose
docker-compose -f docker-compose.dev.yml up
```

#### Option 3: Conda Environment

```bash
# Create conda environment
conda create -n req2run python=3.11

# Activate environment
conda activate req2run

# Install pip packages
pip install -r requirements.txt

# Or use conda-specific packages
conda install pandas numpy click tqdm -c conda-forge
```

#### Option 4: Poetry (Advanced)

```bash
# Install poetry if not already installed
pip install --user poetry

# Install dependencies
poetry install

# Activate shell
poetry shell

# Run commands within poetry environment
poetry run python your_script.py
```

### System-Specific Instructions

#### Ubuntu/Debian

```bash
# Install Python and venv
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate
```

#### macOS

```bash
# Install Python using Homebrew
brew install python@3.11

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate
```

#### Windows

##### Using Windows Store Python
1. Install Python 3.11 from Microsoft Store
2. Open PowerShell or Command Prompt
3. Follow the Windows instructions above

##### Using Python.org installer
1. Download Python 3.11 from python.org
2. During installation, check "Add Python to PATH"
3. Follow the Windows instructions above

### Troubleshooting Common Issues

#### "externally-managed-environment" Error

This error occurs on systems with PEP 668 protection. Solutions:

1. **Use virtual environment** (Recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Use pipx for isolated tools**:
   ```bash
   pipx install click
   pipx install tqdm
   ```

3. **Use --user flag** (Not recommended for development):
   ```bash
   pip install --user -r requirements.txt
   ```

4. **Use --break-system-packages** (Last resort, use with caution):
   ```bash
   pip install --break-system-packages -r requirements.txt
   ```

#### Permission Denied Errors

```bash
# On Linux/Mac
chmod +x scripts/setup-env.sh
./scripts/setup-env.sh

# Or use sudo for system-wide installation (not recommended)
sudo pip install -r requirements.txt
```

#### PowerShell Execution Policy (Windows)

```powershell
# If scripts are blocked, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Development Workflow

1. **Always use a virtual environment** for isolation
2. **Keep requirements.txt updated** when adding dependencies
3. **Test in Docker** before submitting solutions
4. **Document any special dependencies** in your solution README

### IDE Configuration

#### VS Code

1. Install Python extension
2. Select interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose the venv interpreter: `./venv/bin/python`

#### PyCharm

1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Add Local Interpreter
3. Select "Existing environment" and browse to `venv/bin/python`

### Per-Problem Dependencies

Each benchmark problem may have specific dependencies:

```bash
# Navigate to problem directory
cd baselines/WEB-001

# Install problem-specific requirements
pip install -r requirements.txt
```

### Verification

Verify your environment is set up correctly:

```bash
# Check Python version
python --version  # Should be 3.9+

# Check pip packages
pip list

# Run a simple test
python -c "import click, pandas, tqdm; print('All packages imported successfully!')"

# Run benchmark tests
pytest tests/
```

---

<a id="japanese"></a>
## 日本語

### クイックスタート

Req2Runベンチマーク開発を最速で開始する方法：

```bash
# リポジトリをクローン
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark

# 自動セットアップスクリプトを実行
# Linux/Mac用:
./scripts/setup-env.sh

# Windows PowerShell用:
.\scripts\setup-env.ps1

# Windows CMD用:
scripts\setup-env.bat
```

### 手動セットアップオプション

#### オプション1: Python仮想環境（推奨）

##### Linux/Mac
```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip

# 依存関係をインストール
pip install -r requirements.txt
```

##### Windows
```powershell
# 仮想環境を作成
python -m venv venv

# 仮想環境をアクティベート (PowerShell)
.\venv\Scripts\Activate.ps1

# またはCMD用
venv\Scripts\activate.bat

# pipをアップグレード
python -m pip install --upgrade pip

# 依存関係をインストール
pip install -r requirements.txt
```

#### オプション2: Docker環境（最も信頼性が高い）

```bash
# Dockerイメージをビルド
docker build -t req2run-env .

# 開発用にボリュームマウントして実行
docker run -it -v $(pwd):/workspace req2run-env bash

# またはdocker-composeを使用
docker-compose -f docker-compose.dev.yml up
```

#### オプション3: Conda環境

```bash
# conda環境を作成
conda create -n req2run python=3.11

# 環境をアクティベート
conda activate req2run

# pipパッケージをインストール
pip install -r requirements.txt

# またはconda固有のパッケージを使用
conda install pandas numpy click tqdm -c conda-forge
```

#### オプション4: Poetry（上級者向け）

```bash
# poetryがインストールされていない場合はインストール
pip install --user poetry

# 依存関係をインストール
poetry install

# シェルをアクティベート
poetry shell

# poetry環境内でコマンドを実行
poetry run python your_script.py
```

### システム別の手順

#### Ubuntu/Debian

```bash
# Pythonとvenvをインストール
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# 仮想環境を作成してアクティベート
python3.11 -m venv venv
source venv/bin/activate
```

#### macOS

```bash
# HomebrewでPythonをインストール
brew install python@3.11

# 仮想環境を作成してアクティベート
python3.11 -m venv venv
source venv/bin/activate
```

#### Windows

##### Windows Store Pythonを使用
1. Microsoft StoreからPython 3.11をインストール
2. PowerShellまたはコマンドプロンプトを開く
3. 上記のWindows手順に従う

##### Python.orgインストーラーを使用
1. python.orgからPython 3.11をダウンロード
2. インストール中に「Add Python to PATH」をチェック
3. 上記のWindows手順に従う

### よくある問題のトラブルシューティング

#### "externally-managed-environment" エラー

このエラーはPEP 668保護があるシステムで発生します。解決策：

1. **仮想環境を使用**（推奨）：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **pipxで独立したツールを使用**：
   ```bash
   pipx install click
   pipx install tqdm
   ```

3. **--userフラグを使用**（開発には推奨されません）：
   ```bash
   pip install --user -r requirements.txt
   ```

4. **--break-system-packagesを使用**（最終手段、注意して使用）：
   ```bash
   pip install --break-system-packages -r requirements.txt
   ```

#### アクセス拒否エラー

```bash
# Linux/Macの場合
chmod +x scripts/setup-env.sh
./scripts/setup-env.sh

# またはシステム全体のインストール用にsudoを使用（推奨されません）
sudo pip install -r requirements.txt
```

#### PowerShell実行ポリシー（Windows）

```powershell
# スクリプトがブロックされている場合は実行:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# その後、仮想環境をアクティベート
.\venv\Scripts\Activate.ps1
```

### 開発ワークフロー

1. **常に仮想環境を使用**して分離を保つ
2. 依存関係を追加する際は**requirements.txtを更新**
3. ソリューション提出前に**Dockerでテスト**
4. ソリューションのREADMEに**特別な依存関係を文書化**

### IDE設定

#### VS Code

1. Python拡張機能をインストール
2. インタープリターを選択: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. venvインタープリターを選択: `./venv/bin/python`

#### PyCharm

1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Add Local Interpreter
3. "Existing environment"を選択して`venv/bin/python`を参照

### 問題別の依存関係

各ベンチマーク問題には特定の依存関係がある場合があります：

```bash
# 問題ディレクトリに移動
cd baselines/WEB-001

# 問題固有の要件をインストール
pip install -r requirements.txt
```

### 検証

環境が正しくセットアップされていることを確認：

```bash
# Pythonバージョンを確認
python --version  # 3.9以上である必要があります

# pipパッケージを確認
pip list

# 簡単なテストを実行
python -c "import click, pandas, tqdm; print('すべてのパッケージが正常にインポートされました！')"

# ベンチマークテストを実行
pytest tests/
```