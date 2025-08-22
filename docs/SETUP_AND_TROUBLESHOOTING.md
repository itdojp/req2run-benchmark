# Req2Run Setup and Troubleshooting Guide

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## 🚀 Quick Start

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

## 📦 Setup Methods

### Method 1: Python Virtual Environment (Recommended)

#### Linux/Mac
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

#### Windows
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

### Method 2: Docker Environment (Most Reliable)

```bash
# Build the Docker image
docker build -t req2run-env .

# Run with volume mount for development
docker run -it -v $(pwd):/workspace req2run-env bash

# Or use docker-compose
docker-compose -f docker-compose.dev.yml up
```

### Method 3: Conda Environment

```bash
# Create conda environment
conda create -n req2run python=3.11

# Activate environment
conda activate req2run

# Install dependencies
pip install -r requirements.txt
```

### Method 4: Poetry (Advanced)

```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate shell
poetry shell
```

## 🔧 Troubleshooting Common Issues

### Issue 1: "externally-managed-environment" Error

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

#### Solution A: Use Virtual Environment ✅
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

# Install packages normally
pip install -r requirements.txt
```

#### Solution B: Use pipx for CLI Tools
```bash
# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install tools in isolated environments
pipx install click
pipx install tqdm
```

#### Solution C: User Installation
```bash
# Install to user directory
pip install --user -r requirements.txt

# Add user bin to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

#### Solution D: Force Installation ⚠️ (Not Recommended)
```bash
# Override system protection - USE WITH CAUTION
pip install --break-system-packages -r requirements.txt
```

### Issue 2: Permission Denied Errors

**Error Message:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions:**

#### Linux/Mac
```bash
# Option 1: Use virtual environment (best)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Option 2: User installation
pip install --user -r requirements.txt

# Option 3: Fix permissions (if you own the directory)
sudo chown -R $USER:$USER /path/to/python/site-packages
```

#### Windows
```powershell
# Option 1: Run as Administrator
# Right-click PowerShell > Run as Administrator
pip install -r requirements.txt

# Option 2: Use virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue 3: Missing System Dependencies

**Error:** `error: Microsoft Visual C++ 14.0 is required` (Windows)

**Solution:**
```powershell
# Download and install Visual Studio Build Tools
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

# Or install pre-compiled wheels
pip install --only-binary :all: package-name
```

**Error:** `fatal error: Python.h: No such file or directory` (Linux)

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev

# CentOS/RHEL/Fedora
sudo yum install python3-devel

# macOS (with Homebrew)
brew install python
```

### Issue 4: SSL Certificate Errors

**Error:** `SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]`

**Solutions:**

```bash
# Option 1: Update certificates
pip install --upgrade certifi

# Option 2: Use trusted host (temporary)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Option 3: Fix system certificates (macOS)
brew install ca-certificates
```

### Issue 5: Package Version Conflicts

**Error:** `ERROR: pip's dependency resolver does not currently take into account all the packages that are installed`

**Solutions:**

```bash
# Option 1: Create fresh virtual environment
deactivate  # If in a venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Option 2: Use pip-tools for better dependency resolution
pip install pip-tools
pip-compile requirements.in
pip-sync requirements.txt

# Option 3: Install packages one by one
while read package; do
    pip install "$package"
done < requirements.txt
```

### Issue 6: Python Version Mismatch

**Error:** `This version of req2run requires Python >=3.11`

**Solutions:**

```bash
# Check Python version
python --version

# Install Python 3.11+ 
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# macOS with Homebrew
brew install python@3.11

# Windows - Download from python.org
# https://www.python.org/downloads/

# Use pyenv for multiple Python versions
curl https://pyenv.run | bash
pyenv install 3.11.7
pyenv local 3.11.7
```

## 🐳 Docker as Ultimate Fallback

If all else fails, Docker provides a consistent environment:

```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

CMD ["bash"]
```

Build and run:
```bash
docker build -f Dockerfile.dev -t req2run-dev .
docker run -it -v $(pwd):/app req2run-dev
```

## 📋 Platform-Specific Setup Scripts

### Linux/Mac: setup-env.sh
Located at `scripts/setup-env.sh`
- Checks Python version
- Creates virtual environment
- Installs all dependencies
- Sets up pre-commit hooks

### Windows PowerShell: setup-env.ps1
Located at `scripts/setup-env.ps1`
- PowerShell script for Windows
- Handles Windows-specific paths
- Configures execution policy if needed

### Windows CMD: setup-env.bat
Located at `scripts/setup-env.bat`
- Batch script for Command Prompt
- Basic setup for older Windows systems

## 🔍 Verification

After setup, verify your environment:

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Run test command
python -m req2run.cli --help

# Run basic tests
pytest tests/
```

## 📚 Additional Resources

- [Python Virtual Environments Documentation](https://docs.python.org/3/tutorial/venv.html)
- [Docker Documentation](https://docs.docker.com/)
- [pip Documentation](https://pip.pypa.io/)
- [Conda Documentation](https://docs.conda.io/)
- [Poetry Documentation](https://python-poetry.org/docs/)

## 🆘 Getting Help

If you continue to experience issues:

1. Check the [GitHub Issues](https://github.com/itdojp/req2run-benchmark/issues)
2. Join our [Discord Community](https://discord.gg/req2run)
3. Contact support: contact@itdo.jp

---

<a id="japanese"></a>
## 日本語

## 🚀 クイックスタート

Req2Runベンチマーク開発を始める最速の方法：

```bash
# リポジトリのクローン
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark

# 自動セットアップスクリプトの実行
# Linux/Mac:
./scripts/setup-env.sh

# Windows PowerShell:
.\scripts\setup-env.ps1

# Windows CMD:
scripts\setup-env.bat
```

## 📦 セットアップ方法

### 方法1: Python仮想環境（推奨）

#### Linux/Mac
```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip

# 依存関係のインストール
pip install -r requirements.txt
```

#### Windows
```powershell
# 仮想環境の作成
python -m venv venv

# 仮想環境のアクティベート (PowerShell)
.\venv\Scripts\Activate.ps1

# またはCMDの場合
venv\Scripts\activate.bat

# pipのアップグレード
python -m pip install --upgrade pip

# 依存関係のインストール
pip install -r requirements.txt
```

### 方法2: Docker環境（最も信頼性が高い）

```bash
# Dockerイメージのビルド
docker build -t req2run-env .

# 開発用にボリュームマウントして実行
docker run -it -v $(pwd):/workspace req2run-env bash

# またはdocker-composeを使用
docker-compose -f docker-compose.dev.yml up
```

## 🔧 一般的な問題のトラブルシューティング

### 問題1: "externally-managed-environment" エラー

**エラーメッセージ:**
```
error: externally-managed-environment

× この環境は外部で管理されています
```

**解決策A: 仮想環境を使用 ✅**
```bash
# 仮想環境の作成とアクティベート
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate.bat  # Windows

# パッケージを通常通りインストール
pip install -r requirements.txt
```

### 問題2: アクセス拒否エラー

**エラーメッセージ:**
```
ERROR: 環境エラーによりパッケージをインストールできませんでした: [Errno 13] アクセスが拒否されました
```

**解決策:**
```bash
# オプション1: 仮想環境を使用（最良）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# オプション2: ユーザーインストール
pip install --user -r requirements.txt
```

## 🔍 環境の検証

セットアップ後、環境を確認：

```bash
# Pythonバージョンの確認
python --version

# インストール済みパッケージの確認
pip list

# テストコマンドの実行
python -m req2run.cli --help

# 基本テストの実行
pytest tests/
```

## 🆘 ヘルプの取得

問題が続く場合：

1. [GitHubイシュー](https://github.com/itdojp/req2run-benchmark/issues)を確認
2. [Discordコミュニティ](https://discord.gg/req2run)に参加
3. サポートに連絡: contact@itdo.jp