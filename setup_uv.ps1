# ============================================================================
# UV Setup Script for Windows (PowerShell)
# ============================================================================

Write-Host "🚀 AI Retrospective Insights - UV Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if UV is installed
Write-Host "📦 Checking UV installation..." -ForegroundColor Yellow
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvInstalled) {
    Write-Host "❌ UV not found. Installing UV..." -ForegroundColor Red
    pip install uv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install UV. Please install manually: pip install uv" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ UV installed successfully!" -ForegroundColor Green
}
else {
    Write-Host "✅ UV is already installed!" -ForegroundColor Green
}

Write-Host ""

# Create virtual environment
if (Test-Path ".venv") {
    Write-Host "⚠️  Virtual environment already exists at .venv" -ForegroundColor Yellow
    $response = Read-Host "Do you want to recreate it? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "🗑️  Removing old virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force .venv
    }
    else {
        Write-Host "⏭️  Skipping virtual environment creation" -ForegroundColor Yellow
        $skipVenv = $true
    }
}

if (-not $skipVenv) {
    Write-Host "🔨 Creating virtual environment with UV..." -ForegroundColor Yellow
    uv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Virtual environment created!" -ForegroundColor Green
}

Write-Host ""

# Activate and install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
.\.venv\Scripts\activate
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

uv pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Activate the virtual environment:" -ForegroundColor White
Write-Host "     .\.venv\Scripts\activate" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Copy and configure .env file:" -ForegroundColor White
Write-Host "     cp .env.example .env" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Run tests:" -ForegroundColor White
Write-Host "     pytest tests/ -v" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Start the API server:" -ForegroundColor White
Write-Host "     uvicorn src.api.main:app --reload --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Start the Celery worker:" -ForegroundColor White
Write-Host "     celery -A src.core.celery_app worker --loglevel=info --pool=solo" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 For more details, see UV_SETUP.md" -ForegroundColor Cyan
Write-Host ""

