# AI Bot for Retrospective Insights

An AI-powered system that analyzes team metrics and generates actionable retrospective insights with evidence-based hypotheses and experiment suggestions.

## 🎯 Overview

This system acts as an AI Agile Coach, automatically analyzing sprint metrics to:

- **Surface trends** that are easy to miss
- **Generate evidence-backed hypotheses** about team performance
- **Suggest concrete experiments** to improve in the next sprint
- **Provide facilitation guides** for productive retrospectives

## ✨ Key Features

### 🆕 Dashboard Integration & AI Agent (NEW!)

- **Real-time Dashboard Data**: Integrated with N8N webhooks for live metrics
- **LangGraph AI Agent**: Intelligent analysis using state-based reasoning
- **Natural Language Queries**: Ask questions in plain English
- **Auto Chart Selection**: AI determines relevant data automatically
- **Smart Insights**: GPT-4-powered recommendations

### Automated Analysis

- **Statistical Analysis**: Trend detection, correlation analysis, anomaly detection
- **Hypothesis Generation**: Rule-based templates identify patterns (review bottlenecks, story sizing issues, quality degradation, team morale, workflow efficiency)
- **Experiment Suggestions**: Actionable, timeboxed experiments mapped to each hypothesis
- **LLM Integration**: OpenAI/Anthropic for narrative generation and enhanced insights

### Comprehensive Metrics Support

- Team happiness
- Story point distribution
- Items out of sprint (carryover %)
- Defect rates (production, all environments)
- Bugs by environment (PROD/ACC/TEST/DEV/OTHER)
- Bug root causes (testing gaps, requirement gaps, etc.)
- Time metrics (coding, review, testing)

### Output

- **Headline**: Compelling 1-2 line summary
- **Interactive Charts**: Plotly visualizations (trends, distributions, correlations)
- **Top 3 Hypotheses**: With confidence levels and evidence
- **1-3 Experiments**: Concrete actions with success metrics
- **Facilitation Guide**: Retro questions + 15-minute agenda

## 🏗️ Architecture

```
┌─────────────────┐
│  External API   │ ← Fetch team metrics
└────────┬────────┘
         │
┌────────▼────────┐
│ Metrics Client  │
└────────┬────────┘
         │
┌────────▼────────┐
│   Statistical   │ → Trends, Correlations, Patterns
│    Analysis     │
└────────┬────────┘
         │
┌────────▼────────┐
│   Hypothesis    │ → Top 3 Evidence-Based Hypotheses
│   Generator     │
└────────┬────────┘
         │
┌────────▼────────┐
│   Experiment    │ → Actionable Suggestions
│   Generator     │
└────────┬────────┘
         │
┌────────▼────────┐
│  LLM Integration│ → Enhanced Narratives
└────────┬────────┘
         │
┌────────▼────────┐
│ Chart Generator │ → Interactive Visualizations
└────────┬────────┘
         │
┌────────▼────────┐
│     Report      │ → Complete Retrospective Report
│   Assembler     │
└─────────────────┘
```

## 📦 Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Async Tasks**: Celery + Redis
- **Analysis**: Pandas, NumPy, SciPy
- **Visualization**: Plotly
- **LLM**: OpenAI / Anthropic APIs
- **Testing**: Pytest (146 tests, 135+ passing ✅)
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS

## ✅ Current Implementation Status

### ✅ Completed (Phases 1-6)

- [x] **Phase 1-2**: Core infrastructure (config, models, database)
- [x] **Phase 2**: External API client with retry logic
- [x] **Phase 2**: Statistical analysis engine (trends, correlations, anomalies)
- [x] **Phase 3**: Hypothesis generation (6 pattern types)
- [x] **Phase 3**: Experiment suggestion engine
- [x] **Phase 3**: LLM integration (OpenAI/Anthropic)
- [x] **Phase 4**: Chart generation (Plotly)
- [x] **Phase 4**: Report assembler
- [x] **Phase 5**: FastAPI routers and endpoints
- [x] **Phase 6**: Celery async tasks (23/23 tests passing)
  - Async report generation
  - Async metrics syncing
  - Task status tracking
  - Task management API

### ✅ Completed (Phase 7)

- [x] **Full React Dashboard** - Professional TypeScript app with:
  - Interactive dashboard with stats overview
  - Reports management (list, view, delete, search)
  - Full report detail view with interactive charts
  - Hypothesis cards with evidence
  - Experiment suggestions with implementation steps
  - Async task monitoring
  - Responsive design with Tailwind CSS

## 🧪 Testing

```bash
# Option A) Using UV (no manual activation needed)
uv run pytest tests/ -v
uv run pytest tests/ --cov=src --cov-report=html

# Option B) Using the virtual environment directly
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html

# Current status: 146 tests (135+ passing ✅)
```

## 🚀 Quick Start

### Using UV (Recommended - 10x faster!)

```bash
# 1. Install UV
pip install uv

# 2. Create virtual environment
uv venv

# 3. Activate virtual environment
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 4. Install dependencies
uv pip install -e ".[dev]"
```

See [UV_SETUP.md](UV_SETUP.md) for detailed UV usage guide.

### Using pip (Traditional)

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start services with Docker
docker-compose up -d

# 4. Initialize database
python -c "from src.core.database import init_db; init_db()"

# 5. Start Celery worker (in separate terminal)
celery -A src.core.celery_app worker --loglevel=info --pool=solo

# 6. Start FastAPI server
uvicorn src.api.main:app --reload

# 7. Run tests
pytest tests/ -v

# 8. Start Frontend (separate terminal)
cd frontend
npm install
npm run dev
# Frontend will be at http://localhost:3000
```

## 📊 Example Report Structure

```json
{
  "report_id": "RPT-20241015-abc123",
  "headline": "Review time increased 50% while defect rate doubled - quality bottleneck",
  "sprint_period": "Sprint 24.01 - Sprint 24.05",
  "hypotheses": [
    {
      "title": "Review Process Bottleneck",
      "confidence": "High",
      "confidence_score": 0.85,
      "evidence": [
        {"metric_name": "review_time", "trend": "up 50%", "value": "20 → 30 hours"}
      ]
    }
  ],
  "experiments": [
    {
      "title": "Implement WIP Limit for Code Review",
      "success_metrics": ["review_time", "pr_lead_time"],
      "expected_outcome": "Reduce review time by 20-30%"
    }
  ],
  "facilitation_notes": {
    "retro_questions": [
      "What's causing the review bottleneck?",
      "How does this affect team effectiveness?",
      "What experiment should we try?"
    ],
    "agenda_15min": ["Review metrics (5 min)", "Discuss hypotheses (7 min)", ...]
  }
}
```

## 🎓 Key Algorithms

### Trend Detection

- Month-over-month % change calculation
- Significance threshold (>20% change)
- Z-score anomaly detection
- Moving averages (3-month, 5-month)

### Hypothesis Generation

- **Pattern Matching**: 6 hypothesis templates
- **Evidence Collection**: Link supporting metrics
- **Confidence Scoring**: Based on correlation strength and magnitude
- **Ranking**: Top 3 by confidence score

### Experiment Suggestions

- Mapped to hypothesis types
- Timeboxed (1-sprint duration)
- Measurable success metrics
- Concrete implementation steps

## 📖 Success Metrics

- Report generation time: <5 minutes ⏱️
- Test coverage: 92%+ 📊
- Experiment adoption: Target >70% 🎯
- Metric improvements: 15-30% over 3 sprints 📈

## 🤝 Contributing

This is an experimental AI system for improving team retrospectives. Contributions welcome!

## 📝 License

MIT License - See LICENSE file for details
