# Dashboard Integration & AI Agent Implementation

## Overview

This implementation integrates the N8N webhook API for dashboard data and adds an AI agent powered by LangGraph for intelligent analysis and insights generation.

## 🎯 Features Implemented

### 1. Dashboard Data Client (`src/utils/dashboard_client.py`)

A robust client for fetching dashboard chart data from N8N webhooks with:

- **Automatic Token Management**: Fetches and refreshes authentication tokens (300s expiry)
- **Smart Retry Logic**: Automatically retries on authentication errors
- **Type-Safe API**: Uses TypedDict for chart types
- **Comprehensive Error Handling**: Custom exceptions for better error tracking

#### Supported Chart Types

1. `testing-time` - Time spent on testing activities
2. `review-time` - Time spent on code review
3. `coding-time` - Time spent on coding
4. `root-cause` - Root causes of bugs and issues
5. `open-bugs-over-time` - Trend of open bugs over time
6. `bugs-per-environment` - Bug distribution by environment
7. `sp-distribution` - Story point distribution
8. `items-out-of-sprint` - Items carried over from sprint
9. `defect-rate-prod` - Defect rate in production
10. `defect-rate-all` - Overall defect rate
11. `happiness` - Team happiness scores

#### API Endpoints

```python
# Get Token (expires in 300s)
GET https://n8n.idp.infodation.vn/webhook/88eda05f-41d5-4ce4-b836-cb0f1bba3b2e

# Get Chart Data
GET https://n8n.idp.infodation.vn/webhook/39c5b0e5-4aca-4964-a718-5d3deeebed25
Headers:
  Authorization: Bearer <token>
Params:
  name: <chart_name>
```

#### Usage Example

```python
from src.utils.dashboard_client import get_dashboard_client

client = get_dashboard_client()

# Fetch single chart
data = await client.fetch_chart_data("happiness")

# Fetch multiple charts
charts = await client.fetch_multiple_charts(["happiness", "defect-rate-all"])

# Fetch all charts
all_data = await client.fetch_all_charts()
```

### 2. LangGraph AI Agent (`src/analysis/langgraph_agent.py`)

An intelligent agent that uses LangGraph state machine for structured analysis:

#### Agent Workflow

```
┌──────────────┐
│ User Query   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Analyze Query │ ← Determine relevant charts using LLM
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Fetch Data   │ ← Get chart data from N8N API
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Analyze Data  │ ← Statistical analysis (trends, anomalies)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Generate   │ ← LLM-powered insights & recommendations
│  Insights    │
└──────────────┘
```

#### Key Features

- **Context-Aware**: Analyzes user query to determine relevant data
- **Statistical Analysis**: Detects trends, anomalies, and patterns
- **LLM-Enhanced**: Uses GPT-4 for natural language insights
- **Actionable**: Provides concrete recommendations

#### Usage Example

```python
from src.analysis.langgraph_agent import get_dashboard_agent

agent = get_dashboard_agent()

# Full analysis
result = await agent.analyze("How is team happiness trending?")
# Returns: {
#   "success": True,
#   "query": "...",
#   "insights": "Team happiness has decreased...",
#   "chart_data": {...},
#   "analysis": {...}
# }

# Simple chat
response = await agent.chat("What's the current defect rate?")
```

### 3. Dashboard API Endpoints (`src/api/routers/dashboard.py`)

RESTful API endpoints for accessing dashboard data and AI insights:

#### Endpoints

##### 1. Health Check
```http
GET /dashboard/health
```

##### 2. Get Single Chart
```http
GET /dashboard/charts/{chart_name}

Response:
{
  "chart_name": "happiness",
  "data": {...},
  "success": true
}
```

##### 3. Get Multiple Charts
```http
GET /dashboard/charts?chart_names=happiness&chart_names=defect-rate-all

Response:
{
  "charts": {...},
  "success": true,
  "total_charts": 2
}
```

##### 4. Generate AI Insights
```http
POST /dashboard/insights

Body:
{
  "query": "How is team performance?",
  "include_chart_data": true
}

Response:
{
  "query": "How is team performance?",
  "insights": "Team happiness is declining...",
  "analysis": {...},
  "chart_data": {...},
  "success": true
}
```

##### 5. Chat with AI Agent
```http
POST /dashboard/chat?message=What's happening with bugs?

Response:
{
  "message": "What's happening with bugs?",
  "response": "Bug counts are increasing...",
  "success": true
}
```

##### 6. List Available Charts
```http
GET /dashboard/available-charts

Response:
{
  "charts": [
    {
      "name": "happiness",
      "description": "Team happiness and satisfaction scores",
      "category": "team-health"
    },
    ...
  ],
  "total": 11
}
```

## 🚀 Setup & Installation

### 1. Install Dependencies

```bash
# Using UV (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install langgraph langchain langchain-openai langchain-core
```

### 2. Environment Configuration

Add to your `.env` file:

```env
# OpenAI API Key (for AI agent)
OPENAI_API_KEY=your_openai_api_key_here

# N8N webhooks are hardcoded in the client
# No additional configuration needed
```

### 3. Run the Application

```bash
# Start the API server
uvicorn src.api.main:app --reload

# Or using Docker
docker-compose up
```

## 📊 Example Use Cases

### Use Case 1: Team Health Check

```bash
curl -X POST "http://localhost:8000/dashboard/insights" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Give me a comprehensive team health report",
    "include_chart_data": true
  }'
```

**Response:**
```json
{
  "query": "Give me a comprehensive team health report",
  "insights": "Team Happiness: Currently at 6.5/10, down from 7.5 last month (-13.3%). This decline correlates with an increase in defect rates (now at 20%, up from 10%). Recommendations: 1) Review workload distribution, 2) Increase code review time, 3) Team retrospective on quality practices.",
  "analysis": {
    "relevant_charts": ["happiness", "defect-rate-all", "review-time"],
    "trends": [
      {"chart": "happiness", "direction": "decreasing", "change": "13.3%"},
      {"chart": "defect-rate-all", "direction": "increasing", "change": "100%"}
    ]
  },
  "success": true
}
```

### Use Case 2: Quality Analysis

```bash
curl -X POST "http://localhost:8000/dashboard/chat?message=What%27s%20causing%20the%20bug%20spike%3F"
```

**Response:**
```json
{
  "message": "What's causing the bug spike?",
  "response": "The bug spike is primarily driven by two factors: 1) Root cause analysis shows 40% are due to missed testing scenarios, and 2) Bugs are concentrated in the TEST environment (45%), suggesting issues are being caught before production. This is actually a positive sign - your testing is effective. However, consider improving test coverage in early development stages.",
  "success": true
}
```

### Use Case 3: Sprint Planning Insights

```bash
curl -X GET "http://localhost:8000/dashboard/charts?chart_names=sp-distribution&chart_names=items-out-of-sprint"
```

## 🧪 Testing

Comprehensive test suites have been created:

### Run All Tests

```bash
# Using UV
uv run pytest tests/ -v

# Or with virtual environment
pytest tests/test_dashboard_client.py -v
pytest tests/test_langgraph_agent.py -v
```

### Test Coverage

- **Dashboard Client**: 11 tests covering token management, data fetching, error handling
- **LangGraph Agent**: 11 tests covering all workflow steps, error handling, formatting

## 🔐 Security Considerations

1. **Token Management**: Tokens automatically expire after 300 seconds
2. **Environment Variables**: API keys stored securely in `.env`
3. **Error Handling**: No sensitive data leaked in error messages
4. **CORS**: Configure properly for production (currently allows all origins)

## 📈 Performance

- **Token Caching**: Reduces API calls by reusing valid tokens
- **Async Operations**: All I/O operations are non-blocking
- **Batch Fetching**: Can fetch multiple charts in parallel
- **LLM Optimization**: Uses GPT-4o-mini for faster responses

## 🛠️ Troubleshooting

### Issue: Token Expired Error

```python
# Force token refresh
from src.utils.dashboard_client import get_dashboard_client
client = get_dashboard_client()
client.invalidate_token()
```

### Issue: LLM Rate Limits

```python
# Reduce temperature or switch models
from src.analysis.langgraph_agent import DashboardAnalysisAgent
agent = DashboardAnalysisAgent(model_name="gpt-3.5-turbo", temperature=0.5)
```

### Issue: Slow Response Times

- Use `include_chart_data=False` in insights requests
- Fetch specific charts instead of all charts
- Consider caching frequent queries

## 🔄 Integration with Existing System

The dashboard integration seamlessly integrates with your existing retrospective insights system:

```python
# In your analysis pipeline
from src.utils.dashboard_client import get_dashboard_client
from src.analysis.langgraph_agent import get_dashboard_agent

# Fetch real-time dashboard data
client = get_dashboard_client()
current_metrics = await client.fetch_all_charts()

# Use AI agent for enhanced analysis
agent = get_dashboard_agent()
insights = await agent.analyze(
    "Compare current sprint metrics with historical trends"
)

# Combine with existing hypothesis generation
from src.analysis.hypothesis import HypothesisGenerator
hypothesis_gen = HypothesisGenerator()
hypotheses = hypothesis_gen.generate_hypotheses(current_metrics)
```

## 📚 API Documentation

Full interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎓 Learning Resources

- **LangGraph Documentation**: https://python.langchain.com/docs/langgraph
- **LangChain Guide**: https://python.langchain.com/docs/get_started/introduction
- **FastAPI Best Practices**: https://fastapi.tiangolo.com/

## ✅ Implementation Checklist

- [x] Dashboard data client with N8N webhook integration
- [x] Automatic token management with refresh logic
- [x] LangGraph-based AI agent with state machine
- [x] Statistical analysis of chart data
- [x] LLM-powered insights generation
- [x] RESTful API endpoints
- [x] Comprehensive test suites
- [x] Error handling and logging
- [x] Documentation and examples

## 🚀 Next Steps

1. **Deploy to Production**: Configure proper CORS and environment variables
2. **Add Caching**: Implement Redis caching for frequently accessed data
3. **Enhanced Analytics**: Add more sophisticated statistical analysis
4. **Custom Visualizations**: Generate charts based on AI insights
5. **Slack Integration**: Send AI insights to Slack channels
6. **Monitoring**: Add metrics tracking for API usage

## 📞 Support

For issues or questions:
- Check the API documentation at `/docs`
- Review test files for usage examples
- Check logs for detailed error information

---

**Implementation Date**: October 30, 2025  
**Version**: 1.0.0  
**Status**: ✅ Complete and Ready for Use
