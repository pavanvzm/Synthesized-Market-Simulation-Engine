#!/bin/bash
# setup.sh - Automated setup script for Synthesized Market Simulation Engine
set -e

echo "=== Synthesized Market Simulation Engine Setup ==="

# 1. Ensure required directories exist
echo "Creating required directories..."
mkdir -p data/sim/runs
mkdir -p data/sample
mkdir -p reports
mkdir -p logs
mkdir -p .qdrant_storage
mkdir -p .cache
mkdir -p tests
echo "✓ Directories initialized."

# 2. Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed. Please install Python 3.9+."
    exit 1
else
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "✓ Python version $PYTHON_VERSION detected."
fi

# 3. Create .env if not exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "✓ .env file created. Please customize it with your settings."
    else
        echo "⚠️ Warning: .env.example not found. Creating a minimal .env file..."
        cat <<EOT > .env
LLM_PROVIDER=mock
RESOURCE_PROFILE=low
QDRANT_MODE=local
RANDOM_SEED=42
EOT
        echo "✓ Minimal .env file created."
    fi
else
    echo "✓ .env file already exists."
fi

# 4. Install dependencies in editable mode for current environment
echo "Installing package and development dependencies..."
pip install -e ".[dev]"

echo "=== Setup Completed Successfully ==="
echo "You can now run:"
echo "  sim doctor       - to check your environment health"
echo "  make run-smoke   - to run a quick smoke test simulation"
echo "  pytest tests/ -v - to run the test suite"
