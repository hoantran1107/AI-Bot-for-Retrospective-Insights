#!/bin/bash
# ============================================================================
# UV Setup Script for macOS/Linux
# ============================================================================

echo "🚀 AI Retrospective Insights - UV Setup"
echo "========================================="
echo ""

# Check if UV is installed
echo "📦 Checking UV installation..."
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Installing UV..."
    pip install uv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install UV. Please install manually: pip install uv"
        exit 1
    fi
    echo "✅ UV installed successfully!"
else
    echo "✅ UV is already installed!"
fi

echo ""

# Create virtual environment
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment already exists at .venv"
    read -p "Do you want to recreate it? (y/N): " response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        echo "🗑️  Removing old virtual environment..."
        rm -rf .venv
    else
        echo "⏭️  Skipping virtual environment creation"
        skipVenv=true
    fi
fi

if [ -z "$skipVenv" ]; then
    echo "🔨 Creating virtual environment with UV..."
    uv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created!"
fi

echo ""

# Activate and install dependencies
echo "📥 Installing dependencies..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

uv pip install -e ".[dev]"
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Copy and configure .env file:"
echo "     cp .env.example .env"
echo ""
echo "  3. Run tests:"
echo "     pytest tests/ -v"
echo ""
echo "  4. Start the API server:"
echo "     uvicorn src.api.main:app --reload --port 8000"
echo ""
echo "  5. Start the Celery worker:"
echo "     celery -A src.core.celery_app worker --loglevel=info"
echo ""
echo "📖 For more details, see UV_SETUP.md"
echo ""

