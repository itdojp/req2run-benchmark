# Dependency Troubleshooting Guide

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

### Common Dependency Issues and Solutions

This guide helps resolve common dependency installation issues encountered when working with Req2Run benchmarks.

---

## 🚨 Critical Issues

### 1. "externally-managed-environment" Error

**Error Message:**
```
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
```

**Root Cause:** PEP 668 protection prevents pip from modifying system Python packages.

**Solutions (in order of preference):**

#### Solution 1: Use Virtual Environment ✅ (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

# Now install packages normally
pip install -r requirements.txt
```

#### Solution 2: Use pipx for CLI Tools
```bash
# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install tools in isolated environments
pipx install click
pipx install tqdm
```

#### Solution 3: User Installation
```bash
# Install to user directory
pip install --user -r requirements.txt

# Add user bin to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

#### Solution 4: Force Installation ⚠️ (Not Recommended)
```bash
# Override system protection - USE WITH CAUTION
pip install --break-system-packages -r requirements.txt
```

---

### 2. Permission Denied Errors

**Error Message:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions:**

#### On Linux/Mac:
```bash
# Option 1: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Option 2: User installation
pip install --user -r requirements.txt

# Option 3: Fix permissions (if you own the directory)
sudo chown -R $(whoami) /path/to/problematic/directory
```

#### On Windows:
```powershell
# Run as Administrator or use virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

### 3. Package Not Found / Version Conflicts

**Error Messages:**
- `ERROR: Could not find a version that satisfies the requirement`
- `ERROR: No matching distribution found for`

**Solutions:**

```bash
# Update pip first
pip install --upgrade pip

# Try installing from different index
pip install -r requirements.txt --index-url https://pypi.org/simple

# Install specific versions
pip install "pandas>=2.0.0,<3.0.0"

# Use conda for complex dependencies
conda install pandas numpy scipy -c conda-forge
```

---

### 4. Build/Compilation Errors

**Common with:** numpy, pandas, cryptography, psutil

**Solutions:**

#### Linux:
```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install python3-dev build-essential
sudo apt-get install libssl-dev libffi-dev  # for cryptography

# Then retry installation
pip install -r requirements.txt
```

#### macOS:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install dependencies via Homebrew
brew install openssl libffi

# Set environment variables if needed
export LDFLAGS="-L$(brew --prefix openssl)/lib"
export CFLAGS="-I$(brew --prefix openssl)/include"
```

#### Windows:
```powershell
# Install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or use pre-compiled wheels
pip install --only-binary :all: pandas numpy
```

---

## 📦 Package-Specific Issues

### pandas Installation Issues

```bash
# Try installing without dependencies first
pip install --no-deps pandas

# Then install dependencies
pip install numpy python-dateutil pytz

# Or use conda
conda install pandas
```

### click Installation Issues

```bash
# If click fails, try older version
pip install "click<8.0"

# Or use system package
sudo apt-get install python3-click  # Debian/Ubuntu
brew install click  # macOS with Homebrew
```

### tqdm Installation Issues

```bash
# Simple alternative if tqdm fails
pip install alive-progress  # Alternative progress bar

# Or implement basic progress without external dependencies
# See baselines/CLI-001 for example
```

---

## 🐳 Docker as Fallback

If dependency issues persist, use Docker:

```bash
# Build Docker image with all dependencies
docker build -t req2run-env .

# Run in Docker
docker run -it -v $(pwd):/app req2run-env bash

# Or use docker-compose
docker-compose up
```

**Dockerfile template for problem solving:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "your_solution.py"]
```

---

## 🔧 Environment Variables

Sometimes setting environment variables helps:

```bash
# Ignore pip version check
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Use different pip cache
export PIP_CACHE_DIR=/tmp/pip-cache

# Increase timeout for slow connections
export PIP_DEFAULT_TIMEOUT=100

# Use specific Python version
export PYTHON_VERSION=3.11
```

---

## 🎯 Platform-Specific Solutions

### WSL (Windows Subsystem for Linux)

```bash
# Update WSL first
wsl --update

# Install Python in WSL
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Create venv in WSL
python3.11 -m venv venv
source venv/bin/activate
```

### Anaconda/Miniconda

```bash
# Create conda environment
conda create -n req2run python=3.11

# Activate environment
conda activate req2run

# Install pip packages in conda
conda install pip
pip install -r requirements.txt
```

### Google Colab

```python
# In notebook cell
!pip install click pandas tqdm

# Mount drive if needed
from google.colab import drive
drive.mount('/content/drive')
```

---

## 💡 Prevention Tips

1. **Always use virtual environments**
2. **Keep pip updated:** `pip install --upgrade pip`
3. **Document your Python version:** `python --version > .python-version`
4. **Use requirements.txt with versions:** `pip freeze > requirements.txt`
5. **Test in Docker before submission**
6. **Have fallback implementations without external dependencies**

---

## 🆘 Getting Help

If issues persist:

1. Check the specific problem's README for special requirements
2. Search existing issues: https://github.com/itdojp/req2run-benchmark/issues
3. Create a new issue with:
   - Full error message
   - Python version (`python --version`)
   - Operating system
   - Steps to reproduce

---

<a id="japanese"></a>
## 日本語

### よくある依存関係の問題と解決策

このガイドは、Req2Runベンチマークで作業する際に遭遇する一般的な依存関係インストールの問題を解決するのに役立ちます。

---

## 🚨 重要な問題

### 1. "externally-managed-environment" エラー

**エラーメッセージ:**
```
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
```

**根本原因:** PEP 668保護により、pipがシステムPythonパッケージを変更することを防いでいます。

**解決策（優先順）:**

#### 解決策1: 仮想環境を使用 ✅（推奨）
```bash
# 仮想環境を作成
python3 -m venv venv

# アクティベート
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate.bat  # Windows

# 通常通りパッケージをインストール
pip install -r requirements.txt
```

#### 解決策2: CLIツールにpipxを使用
```bash
# pipxをインストール
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# 独立した環境にツールをインストール
pipx install click
pipx install tqdm
```

#### 解決策3: ユーザーインストール
```bash
# ユーザーディレクトリにインストール
pip install --user -r requirements.txt

# 必要に応じてユーザーbinをPATHに追加
export PATH="$HOME/.local/bin:$PATH"
```

#### 解決策4: 強制インストール ⚠️（推奨されません）
```bash
# システム保護を上書き - 注意して使用
pip install --break-system-packages -r requirements.txt
```

---

### 2. アクセス拒否エラー

**エラーメッセージ:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**解決策:**

#### Linux/Macの場合:
```bash
# オプション1: 仮想環境を使用（推奨）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# オプション2: ユーザーインストール
pip install --user -r requirements.txt

# オプション3: 権限を修正（ディレクトリを所有している場合）
sudo chown -R $(whoami) /path/to/problematic/directory
```

#### Windowsの場合:
```powershell
# 管理者として実行するか、仮想環境を使用
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

### 3. パッケージが見つからない / バージョンの競合

**エラーメッセージ:**
- `ERROR: Could not find a version that satisfies the requirement`
- `ERROR: No matching distribution found for`

**解決策:**

```bash
# まずpipを更新
pip install --upgrade pip

# 別のインデックスからインストールを試みる
pip install -r requirements.txt --index-url https://pypi.org/simple

# 特定のバージョンをインストール
pip install "pandas>=2.0.0,<3.0.0"

# 複雑な依存関係にはcondaを使用
conda install pandas numpy scipy -c conda-forge
```

---

### 4. ビルド/コンパイルエラー

**よくあるパッケージ:** numpy、pandas、cryptography、psutil

**解決策:**

#### Linux:
```bash
# ビルド依存関係をインストール
sudo apt-get update
sudo apt-get install python3-dev build-essential
sudo apt-get install libssl-dev libffi-dev  # cryptography用

# その後、インストールを再試行
pip install -r requirements.txt
```

#### macOS:
```bash
# Xcode Command Line Toolsをインストール
xcode-select --install

# Homebrewで依存関係をインストール
brew install openssl libffi

# 必要に応じて環境変数を設定
export LDFLAGS="-L$(brew --prefix openssl)/lib"
export CFLAGS="-I$(brew --prefix openssl)/include"
```

#### Windows:
```powershell
# Visual C++ Build Toolsをインストール
# ダウンロード先: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# またはプリコンパイル済みホイールを使用
pip install --only-binary :all: pandas numpy
```

---

## 📦 パッケージ固有の問題

### pandasインストールの問題

```bash
# まず依存関係なしでインストールを試みる
pip install --no-deps pandas

# その後、依存関係をインストール
pip install numpy python-dateutil pytz

# またはcondaを使用
conda install pandas
```

### clickインストールの問題

```bash
# clickが失敗した場合、古いバージョンを試す
pip install "click<8.0"

# またはシステムパッケージを使用
sudo apt-get install python3-click  # Debian/Ubuntu
brew install click  # macOS with Homebrew
```

### tqdmインストールの問題

```bash
# tqdmが失敗した場合の簡単な代替
pip install alive-progress  # 代替プログレスバー

# または外部依存関係なしで基本的なプログレスを実装
# 例についてはbaselines/CLI-001を参照
```

---

## 🐳 フォールバックとしてのDocker

依存関係の問題が続く場合は、Dockerを使用：

```bash
# すべての依存関係を含むDockerイメージをビルド
docker build -t req2run-env .

# Dockerで実行
docker run -it -v $(pwd):/app req2run-env bash

# またはdocker-composeを使用
docker-compose up
```

**問題解決用のDockerfileテンプレート:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "your_solution.py"]
```

---

## 🔧 環境変数

環境変数の設定が役立つ場合があります：

```bash
# pipバージョンチェックを無視
export PIP_DISABLE_PIP_VERSION_CHECK=1

# 別のpipキャッシュを使用
export PIP_CACHE_DIR=/tmp/pip-cache

# 遅い接続のタイムアウトを増やす
export PIP_DEFAULT_TIMEOUT=100

# 特定のPythonバージョンを使用
export PYTHON_VERSION=3.11
```

---

## 🎯 プラットフォーム固有の解決策

### WSL (Windows Subsystem for Linux)

```bash
# まずWSLを更新
wsl --update

# WSLにPythonをインストール
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# WSLでvenvを作成
python3.11 -m venv venv
source venv/bin/activate
```

### Anaconda/Miniconda

```bash
# conda環境を作成
conda create -n req2run python=3.11

# 環境をアクティベート
conda activate req2run

# condaでpipパッケージをインストール
conda install pip
pip install -r requirements.txt
```

### Google Colab

```python
# ノートブックセルで
!pip install click pandas tqdm

# 必要に応じてドライブをマウント
from google.colab import drive
drive.mount('/content/drive')
```

---

## 💡 予防のヒント

1. **常に仮想環境を使用**
2. **pipを最新に保つ:** `pip install --upgrade pip`
3. **Pythonバージョンを文書化:** `python --version > .python-version`
4. **バージョン付きrequirements.txtを使用:** `pip freeze > requirements.txt`
5. **提出前にDockerでテスト**
6. **外部依存関係なしのフォールバック実装を用意**

---

## 🆘 ヘルプを得る

問題が続く場合：

1. 特定の問題のREADMEで特別な要件を確認
2. 既存のイシューを検索: https://github.com/itdojp/req2run-benchmark/issues
3. 以下を含む新しいイシューを作成：
   - 完全なエラーメッセージ
   - Pythonバージョン（`python --version`）
   - オペレーティングシステム
   - 再現手順