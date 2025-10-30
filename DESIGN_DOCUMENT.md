# AI Bot for Retrospective Insights - Design Document

**Version:** 1.0  
**Date:** October 30, 2025  
**Author:** Development Team

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [API Design](#api-design)
6. [AI & Machine Learning](#ai--machine-learning)
7. [Database Schema](#database-schema)
8. [External Integrations](#external-integrations)
9. [Security & Configuration](#security--configuration)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### Purpose
The AI Bot for Retrospective Insights is an intelligent system designed to analyze team sprint metrics, identify patterns, generate data-driven hypotheses, and provide actionable recommendations for improving team performance through automated retrospective analysis.

### Key Features
- **Automated Sprint Metrics Analysis**: Statistical analysis of team performance metrics
- **Hypothesis Generation**: AI-powered identification of patterns and potential issues
- **Experiment Suggestions**: Actionable improvement recommendations based on data
- **Real-time Dashboard Integration**: Live data fetching from N8N webhooks
- **LangGraph AI Agent**: Conversational AI for intelligent insights
- **Async Task Processing**: Background job execution with Celery
- **Interactive Visualizations**: Chart generation for data presentation

### Technology Stack
- **Backend Framework**: FastAPI (Python 3.11+)
- **AI/ML**: LangGraph, LangChain, OpenAI GPT-4
- **Task Queue**: Celery with Redis
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Data Science**: NumPy, Pandas, SciPy
- **Testing**: Pytest with 87% coverage
- **Package Management**: UV (fast Python package installer)

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  (Frontend/API Consumers - React, Mobile Apps, CLI Tools)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Health     │  │   Metrics    │  │   Reports    │         │
│  │   Router     │  │   Router     │  │   Router     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │   Tasks      │  │  Dashboard   │                            │
│  │   Router     │  │   Router     │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Statistical      │  │ Hypothesis       │                    │
│  │ Analyzer         │  │ Generator        │                    │
│  └──────────────────┘  └──────────────────┘                    │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Experiment       │  │ Report           │                    │
│  │ Generator        │  │ Assembler        │                    │
│  └──────────────────┘  └──────────────────┘                    │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ LangGraph        │  │ LLM Integration  │                    │
│  │ Agent            │  │ Service          │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ SQLAlchemy ORM   │  │ Database Models  │                    │
│  │                  │  │                  │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   External Services                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   OpenAI     │  │   N8N        │  │   Redis      │         │
│  │   API        │  │   Webhooks   │  │   Queue      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
src/
├── api/                    # API Layer (FastAPI Routes)
│   ├── main.py            # Application entry point
│   ├── dependencies.py    # Dependency injection
│   └── routers/
│       ├── health.py      # Health check endpoints
│       ├── metrics.py     # Sprint metrics CRUD
│       ├── reports.py     # Report generation & retrieval
│       ├── tasks.py       # Async task management
│       └── dashboard.py   # Dashboard & AI insights
│
├── core/                  # Core Infrastructure
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connection & session
│   ├── models.py         # Pydantic data models
│   └── celery_app.py     # Celery task queue setup
│
├── analysis/             # Business Logic & AI
│   ├── statistical.py    # Statistical analysis engine
│   ├── hypothesis.py     # Hypothesis generation
│   ├── experiments.py    # Experiment suggestions
│   ├── report_assembler.py # Report composition
│   ├── llm_integration.py  # OpenAI integration
│   └── langgraph_agent.py  # LangGraph AI agent
│
├── tasks/                # Background Tasks
│   └── analysis_tasks.py # Celery tasks for analysis
│
├── utils/                # Utility Components
│   ├── metrics_client.py # External metrics API client
│   └── dashboard_client.py # N8N webhook client
│
└── charts/               # Visualization
    └── generators.py     # Chart generation utilities
```

---

## Core Components

### 1. API Layer (FastAPI)

#### Main Application (`src/api/main.py`)
- **Purpose**: Application entry point and router registration
- **Key Features**:
  - CORS middleware configuration
  - Router registration (health, metrics, reports, tasks, dashboard)
  - Exception handling
  - Startup/shutdown event handlers

#### Health Router (`src/api/routers/health.py`)
- **Endpoints**:
  - `GET /` - Root endpoint
  - `GET /health` - System health check
- **Purpose**: Service health monitoring and status reporting

#### Metrics Router (`src/api/routers/metrics.py`)
- **Endpoints**:
  - `POST /metrics/fetch` - Fetch and store sprint metrics
  - `GET /metrics` - List all metrics
  - `GET /metrics/{sprint_id}` - Get specific sprint metrics
  - `DELETE /metrics/{sprint_id}` - Delete sprint metrics
- **Purpose**: Sprint metrics CRUD operations

#### Reports Router (`src/api/routers/reports.py`)
- **Endpoints**:
  - `POST /reports/generate` - Generate analysis report
  - `GET /reports` - List all reports
  - `GET /reports/{report_id}` - Get specific report
  - `DELETE /reports/{report_id}` - Delete report
- **Purpose**: Report generation and management

#### Tasks Router (`src/api/routers/tasks.py`)
- **Endpoints**:
  - `POST /tasks/generate-report` - Async report generation
  - `POST /tasks/sync-metrics` - Async metrics sync
  - `GET /tasks/{task_id}` - Get task status
  - `POST /tasks/{task_id}/revoke` - Cancel task
- **Purpose**: Asynchronous task management

#### Dashboard Router (`src/api/routers/dashboard.py`)
- **Endpoints**:
  - `GET /dashboard/health` - Dashboard health check
  - `GET /dashboard/charts/{chart_name}` - Get single chart data
  - `POST /dashboard/charts` - Get multiple charts
  - `POST /dashboard/insights` - Generate AI insights
  - `POST /dashboard/chat` - Conversational AI interface
  - `GET /dashboard/available-charts` - List available charts
- **Purpose**: N8N dashboard integration and AI-powered insights

### 2. Core Infrastructure

#### Configuration (`src/core/config.py`)
- **Purpose**: Centralized configuration management
- **Key Settings**:
  - Database URL
  - Redis connection
  - LLM provider (OpenAI/Anthropic/Azure)
  - API keys and endpoints
  - Analysis thresholds
- **Pattern**: Singleton with Pydantic Settings validation

#### Database (`src/core/database.py`)
- **Purpose**: Database connection and session management
- **Components**:
  - SQLAlchemy engine setup
  - Session factory
  - Base model class
  - Database models (MetricsSnapshot, AnalysisReport, HypothesisDB, ExperimentDB, AnalysisTaskDB)
- **Pattern**: Context manager for session handling

#### Models (`src/core/models.py`)
- **Purpose**: Pydantic models for request/response validation
- **Key Models**:
  - `SprintMetrics` - Sprint performance data
  - `TrendAnalysis` - Trend detection results
  - `CorrelationResult` - Correlation analysis
  - `Hypothesis` - Generated hypotheses
  - `ExperimentSuggestion` - Improvement experiments
  - `RetrospectiveReport` - Complete analysis report
  - `ChartData` - Dashboard chart data

### 3. Analysis Engine

#### Statistical Analyzer (`src/analysis/statistical.py`)
- **Purpose**: Core statistical analysis of sprint metrics
- **Key Methods**:
  - `analyze_trends()` - Time series trend detection
  - `analyze_correlations()` - Metric correlation analysis
  - `detect_anomalies()` - Outlier detection
  - `calculate_moving_average()` - Smoothing trends
  - `analyze_story_point_distribution()` - Work distribution analysis
- **Algorithms**:
  - Linear regression for trends
  - Pearson correlation
  - Z-score anomaly detection
  - Moving average smoothing

#### Hypothesis Generator (`src/analysis/hypothesis.py`)
- **Purpose**: Generate data-driven hypotheses from patterns
- **Detection Methods**:
  - `check_review_bottleneck()` - Code review delays
  - `check_story_sizing_issues()` - Story point problems
  - `check_quality_issues()` - Bug rate patterns
  - `check_team_morale()` - Happiness trends
  - `check_workflow_efficiency()` - Sprint efficiency
  - `check_defect_patterns()` - Bug environment patterns
- **Output**: Hypotheses with evidence and confidence scores

#### Experiment Generator (`src/analysis/experiments.py`)
- **Purpose**: Suggest actionable experiments for improvements
- **Experiment Types**:
  - Review process improvements
  - Story refinement practices
  - Quality assurance enhancements
  - Team morale boosters
  - Workflow optimizations
- **Output**: Detailed experiment plans with success metrics

#### Report Assembler (`src/analysis/report_assembler.py`)
- **Purpose**: Compose complete retrospective reports
- **Process Flow**:
  1. Statistical analysis
  2. Hypothesis generation
  3. Experiment suggestion
  4. Report compilation
  5. Database persistence
- **Output**: Structured `RetrospectiveReport` with all insights

#### LLM Integration (`src/analysis/llm_integration.py`)
- **Purpose**: OpenAI/Azure integration for AI insights
- **Capabilities**:
  - Natural language insight generation
  - Context-aware recommendations
  - Hypothesis refinement
  - Multi-provider support (OpenAI, Azure, Anthropic)

#### LangGraph Agent (`src/analysis/langgraph_agent.py`)
- **Purpose**: Intelligent conversational AI for dashboard analysis
- **Architecture**: State machine with 4 nodes
  1. **analyze_query** - Parse user intent, identify relevant charts
  2. **fetch_data** - Retrieve chart data from N8N
  3. **analyze_data** - Statistical analysis and pattern detection
  4. **generate_insights** - LLM-powered recommendations
- **Features**:
  - Query understanding with LLM
  - Multi-chart analysis
  - Trend detection
  - Conversational interface
  - Context preservation across turns

### 4. Background Tasks

#### Celery Tasks (`src/tasks/analysis_tasks.py`)
- **Purpose**: Asynchronous long-running operations
- **Tasks**:
  - `generate_report_task()` - Background report generation
  - `sync_metrics_task()` - Background metrics fetching
  - `cleanup_old_reports_task()` - Periodic cleanup
- **Benefits**:
  - Non-blocking API responses
  - Progress tracking
  - Retry logic
  - Task revocation

### 5. Utilities

#### Metrics Client (`src/utils/metrics_client.py`)
- **Purpose**: Fetch sprint metrics from external API
- **Features**:
  - HTTP client with retries
  - Authentication handling
  - Mock data fallback for testing
  - Data validation and transformation

#### Dashboard Client (`src/utils/dashboard_client.py`)
- **Purpose**: N8N webhook integration for dashboard data
- **Features**:
  - Automatic token management (300s expiry)
  - Smart retry on authentication errors
  - Support for 11 chart types
  - Batch data fetching
- **Chart Types**:
  - testing-time, review-time, coding-time
  - root-cause, open-bugs-over-time
  - bugs-per-environment, sp-distribution
  - items-out-of-sprint, defect-rate-prod
  - defect-rate-all, happiness

#### Chart Generators (`src/charts/generators.py`)
- **Purpose**: Generate visualization data structures
- **Chart Types**:
  - Bar charts (velocity, bugs)
  - Line charts (trends)
  - Pie charts (distributions)
  - Scatter plots (correlations)
- **Output**: JSON-serializable chart data

---

## Data Flow

### 1. Sprint Metrics Analysis Flow

```
┌─────────────┐
│   Client    │
│  (POST /    │
│  reports/   │
│  generate)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Reports Router  │
│ - Validate req  │
│ - Fetch metrics │
└──────┬──────────┘
       │
       ▼
┌─────────────────────┐
│ Report Assembler    │
│ 1. Statistical      │
│    Analysis         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Statistical Analyzer│
│ - Trends            │
│ - Correlations      │
│ - Anomalies         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Hypothesis Generator│
│ - Review bottleneck │
│ - Story sizing      │
│ - Quality issues    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Experiment Generator│
│ - Process improve.  │
│ - Quality enhance.  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ LLM Integration     │
│ - Refine insights   │
│ - Generate summary  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Database Persist    │
│ - Save report       │
│ - Save hypotheses   │
│ - Save experiments  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Return Report JSON  │
└─────────────────────┘
```

### 2. Dashboard AI Insights Flow

```
┌─────────────┐
│   Client    │
│  (POST /    │
│  dashboard/ │
│  insights)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Dashboard Router    │
│ - Validate query    │
│ - Get agent         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ LangGraph Agent     │
│ Node 1:             │
│ analyze_query()     │
│ - Parse intent      │
│ - Identify charts   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ LangGraph Agent     │
│ Node 2:             │
│ fetch_data()        │
│ - Get token         │
│ - Fetch charts      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Dashboard Client    │
│ - Token management  │
│ - HTTP requests     │
│ - Data fetching     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ N8N Webhook API     │
│ - Token endpoint    │
│ - Data endpoint     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ LangGraph Agent     │
│ Node 3:             │
│ analyze_data()      │
│ - Trends            │
│ - Patterns          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ LangGraph Agent     │
│ Node 4:             │
│ generate_insights() │
│ - LLM analysis      │
│ - Recommendations   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Return Insights     │
└─────────────────────┘
```

### 3. Async Task Flow

```
┌─────────────┐
│   Client    │
│  (POST /    │
│  tasks/     │
│  generate-  │
│  report)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Tasks Router        │
│ - Queue task        │
│ - Return task_id    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Redis Queue         │
│ - Store task        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Celery Worker       │
│ - Pick up task      │
│ - Execute           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Analysis Task       │
│ - Run analysis      │
│ - Update progress   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Database Persist    │
│ - Save results      │
└─────────────────────┘

(Meanwhile, client polls)
┌─────────────┐
│   Client    │
│  (GET /     │
│  tasks/     │
│  {task_id}) │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Tasks Router        │
│ - Check status      │
│ - Return result     │
└─────────────────────┘
```

---

## API Design

### RESTful Principles
- Resource-based URLs
- HTTP methods (GET, POST, DELETE)
- Status codes (200, 201, 404, 422, 500)
- JSON request/response bodies

### Request/Response Patterns

#### Successful Response
```json
{
  "id": "uuid",
  "data": { ... },
  "created_at": "2025-10-30T10:00:00Z"
}
```

#### Error Response
```json
{
  "detail": "Error message"
}
```

#### Paginated Response
```json
{
  "items": [ ... ],
  "total": 100,
  "skip": 0,
  "limit": 10
}
```

### Authentication
- API key authentication via headers
- Token-based auth for N8N webhooks
- Environment variable configuration

---

## AI & Machine Learning

### Statistical Analysis Algorithms

#### 1. Trend Detection
- **Method**: Linear regression
- **Input**: Time series data
- **Output**: Slope, direction, significance
- **Threshold**: 20% change considered significant

#### 2. Correlation Analysis
- **Method**: Pearson correlation coefficient
- **Input**: Paired metric values
- **Output**: Correlation strength (-1 to 1)
- **Threshold**: |r| > 0.6 considered strong

#### 3. Anomaly Detection
- **Method**: Z-score (standard deviations)
- **Input**: Metric values
- **Output**: Outlier identification
- **Threshold**: |z| > 2 considered anomalous

### LLM Integration Architecture

#### Provider Support
1. **OpenAI** (default)
   - Model: gpt-4, gpt-4o-mini
   - Temperature: 0.7
   - Max tokens: 1000

2. **Azure OpenAI**
   - Custom endpoint
   - API version: 2024-02-15-preview
   - Deployment name configuration

3. **Anthropic**
   - Claude models
   - Similar configuration

#### LangGraph State Machine

```python
AgentState = TypedDict('AgentState', {
    'user_query': str,
    'relevant_charts': list[str],
    'chart_data': dict,
    'analysis': dict,
    'insights': str,
    'error': Optional[str]
})
```

**State Transitions**:
- START → analyze_query
- analyze_query → fetch_data
- fetch_data → analyze_data
- analyze_data → generate_insights
- generate_insights → END

### Hypothesis Confidence Scoring

```python
Confidence Levels:
- HIGH: score >= 0.8 (Strong evidence)
- MEDIUM: 0.5 <= score < 0.8 (Moderate evidence)
- LOW: score < 0.5 (Weak evidence)

Score Calculation:
- Trend significance: +0.3
- Strong correlation: +0.3
- Multiple evidence: +0.2
- Recent pattern: +0.2
```

---

## Database Schema

### Entity Relationship Diagram

```
┌────────────────────────┐
│  MetricsSnapshot       │
│────────────────────────│
│  id (PK)               │
│  sprint_id (UNIQUE)    │
│  metrics_data (JSON)   │
│  created_at            │
│  updated_at            │
└────────────────────────┘
            │
            │ 1:N
            ▼
┌────────────────────────┐
│  AnalysisReport        │
│────────────────────────│
│  id (PK)               │
│  report_data (JSON)    │
│  sprint_ids (Array)    │
│  created_at            │
└───────────┬────────────┘
            │
            │ 1:N
            ▼
┌────────────────────────┐
│  HypothesisDB          │
│────────────────────────│
│  id (PK)               │
│  report_id (FK)        │
│  hypothesis_data (JSON)│
│  created_at            │
└────────────────────────┘
            │
            │ 1:N
            ▼
┌────────────────────────┐
│  ExperimentDB          │
│────────────────────────│
│  id (PK)               │
│  report_id (FK)        │
│  experiment_data (JSON)│
│  status (ENUM)         │
│  created_at            │
└────────────────────────┘

┌────────────────────────┐
│  AnalysisTaskDB        │
│────────────────────────│
│  id (PK)               │
│  task_id (UNIQUE)      │
│  task_type             │
│  status                │
│  progress              │
│  result (JSON)         │
│  error_message         │
│  created_at            │
│  updated_at            │
└────────────────────────┘
```

### Table Descriptions

#### MetricsSnapshot
- **Purpose**: Store sprint performance metrics
- **Key Fields**:
  - `sprint_id`: Unique sprint identifier
  - `metrics_data`: JSON blob with all metrics
- **Indexes**: sprint_id (unique)

#### AnalysisReport
- **Purpose**: Store complete retrospective reports
- **Key Fields**:
  - `report_data`: Full report JSON
  - `sprint_ids`: Array of analyzed sprint IDs
- **Relationships**: 1:N with HypothesisDB, ExperimentDB

#### HypothesisDB
- **Purpose**: Store generated hypotheses
- **Key Fields**:
  - `report_id`: Foreign key to AnalysisReport
  - `hypothesis_data`: Hypothesis details JSON
- **Relationships**: N:1 with AnalysisReport

#### ExperimentDB
- **Purpose**: Store experiment suggestions and tracking
- **Key Fields**:
  - `report_id`: Foreign key to AnalysisReport
  - `status`: planned/in_progress/completed/abandoned
- **Relationships**: N:1 with AnalysisReport

#### AnalysisTaskDB
- **Purpose**: Track async task execution
- **Key Fields**:
  - `task_id`: Celery task ID
  - `status`: pending/running/completed/failed
  - `progress`: 0-100%

---

## External Integrations

### 1. N8N Webhook Integration

#### Token Endpoint
- **URL**: `https://n8n.idp.infodation.vn/webhook/88eda05f-41d5-4ce4-b836-cb0f1bba3b2e`
- **Method**: GET
- **Response**: `{"token": "...", "expiresIn": 300}`
- **Purpose**: Obtain authentication token (5-minute validity)

#### Data Endpoint
- **URL**: `https://n8n.idp.infodation.vn/webhook/39c5b0e5-4aca-4964-a718-5d3deeebed25`
- **Method**: GET
- **Authentication**: Bearer token
- **Query Parameters**: `name={chart_name}`
- **Response**: Chart-specific data structure

#### Supported Charts
1. `testing-time` - Time spent on testing activities
2. `review-time` - Code review duration
3. `coding-time` - Active coding time
4. `root-cause` - Bug root cause analysis
5. `open-bugs-over-time` - Bug trend tracking
6. `bugs-per-environment` - Environment-wise bug distribution
7. `sp-distribution` - Story point distribution
8. `items-out-of-sprint` - Incomplete items
9. `defect-rate-prod` - Production defect rate
10. `defect-rate-all` - Overall defect rate
11. `happiness` - Team happiness metrics

#### Client Features
- **Auto-refresh**: Token automatically refreshed before expiry
- **Retry Logic**: Automatic retry on 401 authentication errors
- **Batch Fetching**: Support for fetching multiple charts
- **Error Handling**: Graceful degradation on failures

### 2. OpenAI API Integration

#### Configuration
- **API Key**: Environment variable `CHAT_COMPLETION_API_KEY`
- **Model**: Configurable (default: gpt-4o-mini)
- **Temperature**: 0.7 (balanced creativity)
- **Max Tokens**: 1000

#### Usage Patterns
1. **Hypothesis Refinement**: Enhance generated hypotheses
2. **Insight Generation**: Create natural language summaries
3. **Query Analysis**: Parse user intent in chat interface
4. **Recommendation Generation**: Create actionable advice

### 3. Redis Integration

#### Purpose
- Celery task queue backend
- Task result storage
- Caching layer (potential)

#### Configuration
- **URL**: `redis://localhost:6379/0`
- **Connection Pool**: Managed by Celery

---

## Security & Configuration

### Environment Variables

```bash
# Application
APP_NAME="AI Retrospective Insights"
APP_VERSION="1.0.0"
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL="sqlite:///./retro_insights.db"

# Redis
REDIS_URL="redis://localhost:6379/0"

# External Metrics API
EXTERNAL_METRICS_API_URL=""
EXTERNAL_METRICS_API_KEY=""

# LLM Configuration
LLM_PROVIDER=openai  # openai|anthropic|azure
CHAT_COMPLETION_API_KEY=""
LLM_MODEL=gpt-4o-mini

# Azure OpenAI (if using Azure)
AZURE_ENDPOINT=""
AZURE_API_VERSION=2024-02-15-preview
AZURE_DEPLOYMENT=""

# Analysis Thresholds
DEFAULT_SPRINT_COUNT=5
TREND_THRESHOLD=0.20
CORRELATION_THRESHOLD=0.6
CONFIDENCE_HIGH_THRESHOLD=0.8
CONFIDENCE_MEDIUM_THRESHOLD=0.5
```

### Security Best Practices

1. **API Key Management**
   - Store in environment variables
   - Never commit to version control
   - Rotate regularly

2. **Input Validation**
   - Pydantic model validation
   - SQL injection prevention via ORM
   - Request size limits

3. **CORS Configuration**
   - Configurable allowed origins
   - Credential handling
   - Method restrictions

4. **Error Handling**
   - No sensitive data in error messages
   - Proper HTTP status codes
   - Logging for debugging

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────┐
│  Developer Machine                      │
│  ┌───────────────────────────────────┐ │
│  │  FastAPI (uvicorn)                │ │
│  │  Port: 8000                       │ │
│  └───────────────────────────────────┘ │
│  ┌───────────────────────────────────┐ │
│  │  Celery Worker                    │ │
│  └───────────────────────────────────┘ │
│  ┌───────────────────────────────────┐ │
│  │  Redis (local)                    │ │
│  │  Port: 6379                       │ │
│  └───────────────────────────────────┘ │
│  ┌───────────────────────────────────┐ │
│  │  SQLite Database                  │ │
│  │  File: ./retro_insights.db        │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Docker Deployment

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres
  
  worker:
    build: .
    command: celery -A src.core.celery_app worker
    depends_on:
      - redis
      - postgres
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
```

### Production Considerations

1. **Database**: PostgreSQL for production
2. **Web Server**: Gunicorn with multiple workers
3. **Reverse Proxy**: Nginx for SSL termination
4. **Task Queue**: Separate Celery worker instances
5. **Monitoring**: Health checks, logging, metrics
6. **Scaling**: Horizontal scaling of API and workers

---

## Testing Strategy

### Test Coverage: 87%

### Test Structure

```
tests/
├── test_api_health.py           # Health endpoint tests
├── test_api_metrics.py          # Metrics CRUD tests
├── test_api_reports.py          # Report generation tests
├── test_api_tasks.py            # Async task tests
├── test_dashboard_client.py     # N8N integration tests
├── test_langgraph_agent.py      # AI agent tests
├── test_core_config.py          # Configuration tests
├── test_core_database.py        # Database model tests
├── test_core_models.py          # Pydantic model tests
├── test_statistical.py          # Statistical analysis tests
├── test_hypothesis.py           # Hypothesis generation tests
├── test_experiments.py          # Experiment generation tests
├── test_metrics_client.py       # External API client tests
└── conftest.py                  # Shared fixtures
```

### Testing Patterns

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: API endpoint testing with database
3. **Mocking**: External services (OpenAI, N8N, Redis)
4. **Fixtures**: Shared test data and setup
5. **Async Testing**: pytest-asyncio for async code

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_dashboard_client.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Parallel execution
pytest tests/ -n auto
```

---

## Performance Considerations

### Optimization Strategies

1. **Database**
   - Connection pooling
   - Indexed queries
   - Batch operations

2. **API**
   - Async endpoints
   - Response caching
   - Pagination for large datasets

3. **Background Tasks**
   - Celery for long-running operations
   - Task prioritization
   - Result expiration

4. **LLM Calls**
   - Token limit optimization
   - Response streaming
   - Caching frequent queries

### Scalability

- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Worker Scaling**: Multiple Celery workers for parallel processing
- **Database Scaling**: Read replicas, connection pooling
- **Caching**: Redis for frequently accessed data

---

## Future Enhancements

### Planned Features

1. **Enhanced AI Capabilities**
   - Multi-turn conversations with context
   - Custom model fine-tuning
   - Predictive analytics

2. **Advanced Analytics**
   - Machine learning for pattern recognition
   - Predictive modeling for sprint outcomes
   - Team velocity forecasting

3. **Integration Expansions**
   - Jira/GitHub direct integration
   - Slack notifications
   - Confluence report publishing

4. **User Interface**
   - Web dashboard (React/Vue)
   - Mobile application
   - Interactive visualizations

5. **Collaboration Features**
   - Team comments on reports
   - Experiment tracking and voting
   - Retrospective meeting facilitation

---

## Appendix

### Key Metrics Tracked

- **Velocity**: Story points completed per sprint
- **Testing Time**: Hours spent on testing
- **Review Time**: Code review duration
- **Coding Time**: Active development hours
- **Bug Metrics**: Defects by environment and rate
- **Story Points**: Distribution and completion
- **Team Happiness**: Morale scores
- **Sprint Completion**: Items finished vs. carried over

### Glossary

- **Sprint**: Time-boxed iteration (typically 2 weeks)
- **Story Point**: Unit of work estimation
- **Hypothesis**: Data-driven assumption about team performance
- **Experiment**: Proposed intervention to improve metrics
- **Retrospective**: Team reflection meeting on past sprint
- **LangGraph**: Framework for building stateful AI agents
- **Celery**: Distributed task queue system
- **N8N**: Workflow automation platform

---

**Document Version**: 1.0  
**Last Updated**: October 30, 2025  
**Maintained By**: Development Team
