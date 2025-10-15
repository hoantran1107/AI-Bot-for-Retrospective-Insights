<!-- f5454c7b-319d-4c36-9a44-ba704e90e84b c53ace56-09e9-4194-93a7-298f572f8443 -->
# AI Retrospective Insights System Implementation Plan

## Architecture Overview

Build a FastAPI microservice with:

- **Backend**: FastAPI for API endpoints, Celery for async analysis tasks
- **Analysis Engine**: Hybrid approach (statistical analysis + LLM for narratives)
- **Frontend**: React/Vue dashboard with interactive charts (Plotly/Chart.js)
- **Database**: PostgreSQL for storing historical reports and metrics cache
- **LLM Integration**: OpenAI/Claude API for hypothesis generation and narrative

## Project Structure

```
src/
├── api/                    # FastAPI application
│   ├── main.py            # FastAPI app initialization
│   ├── routers/           # API route handlers
│   │   ├── metrics.py     # Fetch and store metrics from external API
│   │   ├── analysis.py    # Trigger analysis and get reports
│   │   └── dashboard.py   # Dashboard data endpoints
│   └── dependencies.py    # Shared dependencies
├── core/                   # Business logic
│   ├── config.py          # Configuration (API keys, URLs)
│   ├── models.py          # Pydantic models for data validation
│   └── database.py        # Database connection and models
├── analysis/               # Analysis engine
│   ├── statistical.py     # Statistical analysis (trends, correlations)
│   ├── hypothesis.py      # Hypothesis generation logic
│   ├── experiments.py     # Experiment suggestions engine
│   └── llm_integration.py # LLM API calls for narratives
├── tasks/                  # Celery tasks
│   ├── celery_app.py      # Celery configuration
│   └── analysis_tasks.py  # Async analysis tasks
├── charts/                 # Chart generation
│   └── generators.py      # Plotly chart generation logic
├── frontend/               # Web dashboard (React/Vue)
│   ├── public/
│   └── src/
│       ├── components/    # Dashboard components
│       ├── services/      # API client services
│       └── App.jsx        # Main application
├── utils/                  # Utilities
│   ├── metrics_client.py  # Client to fetch from external API
│   └── helpers.py         # Helper functions
└── tests/                  # Unit and integration tests
```

## Implementation Steps

### Phase 1: Core Infrastructure Setup

**1.1 Project Setup**

- Initialize FastAPI project with Poetry/pip requirements
- Setup PostgreSQL database with SQLAlchemy models
- Configure Celery with Redis/RabbitMQ broker
- Create Docker Compose for local development
- Setup environment configuration (.env file)

**1.2 Database Models**

```python
# core/database.py - Key models
- MetricsSnapshot: Store raw metrics for each sprint
- AnalysisReport: Store generated reports
- Hypothesis: Store hypotheses with evidence
- Experiment: Track suggested experiments and results
```

**1.3 External API Integration**

```python
# utils/metrics_client.py
- Fetch metrics from external API
- Transform to standard format
- Handle pagination, errors, retries
```

### Phase 2: Statistical Analysis Engine

**2.1 Trend Analysis** (`analysis/statistical.py`)

- Month-over-month percentage changes
- Moving averages (3-month, 5-month)
- Anomaly detection (Z-score, IQR methods)
- Identify significant shifts (>20% change, statistical significance)

**2.2 Correlation Analysis**

- Pearson correlation matrix between metrics
- Identify metric pairs with strong correlation (|r| > 0.6)
- Lag correlation (e.g., review time impact on bugs next sprint)
- Time series correlation for causal insights

**2.3 Pattern Recognition**

- Story point distribution patterns (concentration in large stories)
- Bug clustering by environment/root cause
- Seasonal patterns in metrics
- Sprint consistency scoring

### Phase 3: AI Hypothesis & Experiment Generation

**3.1 Hypothesis Engine** (`analysis/hypothesis.py`)

- Rule-based hypothesis templates based on metric patterns
- Evidence collection: link supporting metrics with confidence scores
- Ranking: priority score based on impact and confidence
- Output top 3 hypotheses

Example templates:

```python
{
  "pattern": "review_time_up + reopen_rate_up + happiness_down",
  "hypothesis": "Review bottleneck causing quality issues and team frustration",
  "confidence_factors": ["correlation_strength", "magnitude_of_change"],
  "evidence_metrics": ["review_time", "reopen_rate", "happiness"]
}
```

**3.2 LLM Integration** (`analysis/llm_integration.py`)

- Format analysis results as LLM prompt
- Request narrative generation (headline, hypothesis descriptions)
- Parse LLM response into structured format
- Fallback to template-based if LLM fails

**3.3 Experiment Suggestions** (`analysis/experiments.py`)

- Evidence-based experiment templates
- Map hypothesis types to concrete experiments
- Timeboxed, measurable experiments (1-sprint duration)
- Success metrics for each experiment

### Phase 4: Report Generation & Visualization

**4.1 Chart Generation** (`charts/generators.py`)

- Plotly line charts for time series (with annotations)
- Bar charts for distributions (story points, bugs by environment)
- Heatmaps for correlation matrices
- Box plots for time metrics
- Return JSON format for frontend rendering

**4.2 Report Assembly**

- Combine statistical results, hypotheses, charts, experiments
- Generate confidence levels (High/Medium/Low)
- Create evidence links between sections
- Format facilitation notes (3 retro questions + 15-min agenda)

**4.3 Report Model**

```python
class RetrospectiveReport:
  headline: str
  sprint_period: str
  trends: List[TrendAnalysis]
  charts: List[ChartData]
  hypotheses: List[Hypothesis]  # Top 3
  experiments: List[ExperimentSuggestion]  # 1-3
  facilitation_notes: FacilitationGuide
  generated_at: datetime
```

### Phase 5: API Endpoints

**5.1 Metrics Management** (`api/routers/metrics.py`)

```
POST /api/v1/metrics/sync       # Fetch and store latest metrics
GET  /api/v1/metrics/{sprint_id} # Get metrics for specific sprint
```

**5.2 Analysis Endpoints** (`api/routers/analysis.py`)

```
POST /api/v1/analysis/generate   # Trigger report generation (async)
GET  /api/v1/analysis/{report_id} # Get generated report
GET  /api/v1/analysis/latest     # Get latest report
```

**5.3 Dashboard Endpoints** (`api/routers/dashboard.py`)

```
GET /api/v1/dashboard/overview   # Summary for dashboard
GET /api/v1/dashboard/charts     # Chart data
GET /api/v1/dashboard/experiments # Track experiment results
```

### Phase 6: Celery Async Tasks

**6.1 Analysis Task** (`tasks/analysis_tasks.py`)

```python
@celery.task
def generate_retrospective_report(sprint_count=5):
  # 1. Fetch last N sprints metrics
  # 2. Run statistical analysis
  # 3. Generate hypotheses
  # 4. Call LLM for narratives
  # 5. Generate charts
  # 6. Create experiments
  # 7. Assemble and store report
  # 8. Return report_id
```

**6.2 Metrics Sync Task**

```python
@celery.task
def sync_metrics_from_api():
  # Periodic task to fetch latest metrics
```

### Phase 7: Frontend Dashboard

**7.1 Dashboard Components**

- Overview page: headline, key trends, quick stats
- Trends section: interactive charts with drill-down
- Hypotheses section: cards with evidence and confidence
- Experiments section: suggested experiments with tracking
- Historical view: past reports comparison

**7.2 Interactive Features**

- Chart filtering (date range, specific metrics)
- Hypothesis drill-down (show supporting data)
- Experiment tracking (mark as "In Progress", "Completed")
- Export report as PDF
- Share link for team review

**7.3 Technology**

- React + TypeScript (or Vue 3)
- Plotly.js or Chart.js for charts
- TailwindCSS for styling
- React Query for data fetching

### Phase 8: Testing & Documentation

**8.1 Unit Tests**

- Test statistical functions (trend detection, correlation)
- Test hypothesis generation logic
- Mock LLM responses for testing
- Test report assembly

**8.2 Integration Tests**

- Test full analysis pipeline
- Test API endpoints
- Test Celery task execution

**8.3 Documentation**

- API documentation (Swagger/OpenAPI)
- Metrics schema documentation
- Deployment guide (Docker)
- User guide for dashboard

## Key Configuration

**Environment Variables**

```
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
EXTERNAL_METRICS_API_URL=https://...
EXTERNAL_METRICS_API_KEY=...
LLM_PROVIDER=openai  # or anthropic
LLM_API_KEY=...
LLM_MODEL=gpt-4  # or claude-sonnet-4
```

## Success Metrics Implementation

Track in database:

- Report generation time (<5 min target)
- Experiment adoption rate
- User feedback (survey integration)
- Metric improvements over 3 sprints

## Deployment

- Docker containerization
- Docker Compose for local/staging
- Production: Kubernetes or cloud service (AWS ECS, Google Cloud Run)
- CI/CD pipeline (GitHub Actions)

## Timeline Estimate

- Phase 1-2: Core + Statistical Analysis (3-4 days)
- Phase 3: AI Hypothesis & LLM (2-3 days)
- Phase 4-5: Reports & APIs (2-3 days)
- Phase 6-7: Async Tasks & Frontend (4-5 days)
- Phase 8: Testing & Polish (2 days)

**Total: ~14-17 days of focused development**

### To-dos

- [ ] Initialize FastAPI project structure, setup Poetry/requirements, configure PostgreSQL + SQLAlchemy models, setup Celery with Redis, create Docker Compose
- [ ] Build metrics client to fetch data from external API, handle transformations, errors, and retries
- [ ] Implement statistical analysis functions: trend detection, correlation analysis, anomaly detection, pattern recognition
- [ ] Build hypothesis generation engine with rule-based templates, evidence collection, and ranking logic
- [ ] Integrate LLM API (OpenAI/Claude) for narrative generation, headline creation, and hypothesis descriptions
- [ ] Create experiment suggestion engine that maps hypotheses to concrete, timeboxed experiments
- [ ] Implement chart generation with Plotly: time series, bar charts, heatmaps, box plots, return JSON for frontend
- [ ] Build report assembly logic combining all components: trends, hypotheses, experiments, charts, facilitation notes
- [ ] Create FastAPI routers for metrics, analysis, and dashboard endpoints with proper validation
- [ ] Implement Celery tasks for async report generation and metrics syncing
- [ ] Build React/Vue dashboard with interactive charts, hypothesis cards, experiments tracking, and report export
- [ ] Write unit tests for analysis functions, integration tests for API, mock LLM responses
- [ ] Create API docs (Swagger), deployment guide, user guide, and metrics schema documentation