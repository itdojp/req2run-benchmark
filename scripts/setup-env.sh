#!/bin/bash

# Req2Run Benchmark Environment Setup Script
# For Linux and macOS systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Header
echo "=================================="
echo "Req2Run Benchmark Environment Setup"
echo "=================================="
echo ""

# Check Python version
print_status "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.9+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.9 or higher"
    exit 1
fi

# Check if virtual environment already exists
if [ -d "venv" ]; then
    print_warning "Virtual environment 'venv' already exists"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing existing virtual environment..."
        rm -rf venv
    else
        print_status "Using existing virtual environment"
    fi
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -eq 0 ]; then
        print_status "Virtual environment created successfully"
    else
        print_error "Failed to create virtual environment"
        print_warning "Trying alternative method with virtualenv..."
        
        # Try installing virtualenv
        pip3 install --user virtualenv
        virtualenv venv
        
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment with virtualenv"
            exit 1
        fi
    fi
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements if file exists
if [ -f "requirements.txt" ]; then
    print_status "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_status "Dependencies installed successfully"
    else
        print_warning "Some dependencies failed to install"
        print_warning "You may need to install them manually"
    fi
else
    print_warning "requirements.txt not found in current directory"
fi

# Install commonly needed packages for benchmarks
print_status "Installing common benchmark packages..."
pip install click pandas numpy tqdm pytest 2>/dev/null || true

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << EOF
# Req2Run Environment Configuration
PYTHONPATH=.
REQ2RUN_ENV=development
EOF
fi

# Final instructions
echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate the virtual environment, run:"
echo "  deactivate"
echo ""
echo "To install problem-specific dependencies:"
echo "  cd baselines/[PROBLEM-ID]"
echo "  pip install -r requirements.txt"
echo ""
print_status "Environment setup completed successfully!"