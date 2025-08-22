# Req2Run Benchmark Environment Setup Script
# For Windows PowerShell

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success {
    Write-Host "[✓] " -ForegroundColor Green -NoNewline
    Write-Host $args[0]
}

function Write-Error-Message {
    Write-Host "[✗] " -ForegroundColor Red -NoNewline
    Write-Host $args[0]
}

function Write-Warning-Message {
    Write-Host "[!] " -ForegroundColor Yellow -NoNewline
    Write-Host $args[0]
}

# Header
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Req2Run Benchmark Environment Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Success "Checking Python version..."
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -ge 3 -and $minor -ge 9) {
            Write-Success "Python $major.$minor found"
        } else {
            Write-Error-Message "Python 3.9+ required, found $major.$minor"
            exit 1
        }
    } else {
        Write-Error-Message "Could not determine Python version"
        exit 1
    }
} catch {
    Write-Error-Message "Python not found. Please install Python 3.9 or higher"
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment already exists
if (Test-Path "venv") {
    Write-Warning-Message "Virtual environment 'venv' already exists"
    $response = Read-Host "Do you want to recreate it? (y/n)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Success "Removing existing virtual environment..."
        Remove-Item -Recurse -Force venv
    } else {
        Write-Success "Using existing virtual environment"
    }
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Success "Creating virtual environment..."
    try {
        python -m venv venv
        Write-Success "Virtual environment created successfully"
    } catch {
        Write-Error-Message "Failed to create virtual environment"
        Write-Warning-Message "Trying alternative method with virtualenv..."
        
        # Try installing virtualenv
        pip install --user virtualenv
        virtualenv venv
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to create virtual environment with virtualenv"
            exit 1
        }
    }
}

# Activate virtual environment
Write-Success "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Check if activation was successful
if ($env:VIRTUAL_ENV) {
    Write-Success "Virtual environment activated"
} else {
    Write-Warning-Message "Virtual environment activation may have failed"
    Write-Warning-Message "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
}

# Upgrade pip
Write-Success "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements if file exists
if (Test-Path "requirements.txt") {
    Write-Success "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed successfully"
    } else {
        Write-Warning-Message "Some dependencies failed to install"
        Write-Warning-Message "You may need to install them manually"
    }
} else {
    Write-Warning-Message "requirements.txt not found in current directory"
}

# Install commonly needed packages for benchmarks
Write-Success "Installing common benchmark packages..."
pip install click pandas numpy tqdm pytest 2>$null

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Success "Creating .env file..."
    @"
# Req2Run Environment Configuration
PYTHONPATH=.
REQ2RUN_ENV=development
"@ | Out-File -FilePath ".env" -Encoding UTF8
}

# Final instructions
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To activate the virtual environment in the future, run:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To deactivate the virtual environment, run:" -ForegroundColor Yellow
Write-Host "  deactivate" -ForegroundColor White
Write-Host ""
Write-Host "To install problem-specific dependencies:" -ForegroundColor Yellow
Write-Host "  cd baselines\[PROBLEM-ID]" -ForegroundColor White
Write-Host "  pip install -r requirements.txt" -ForegroundColor White
Write-Host ""
Write-Host "If you encounter execution policy errors, run:" -ForegroundColor Yellow
Write-Host "  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
Write-Host ""
Write-Success "Environment setup completed successfully!"