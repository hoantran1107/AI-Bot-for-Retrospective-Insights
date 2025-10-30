# Quick Start: Dashboard Integration & AI Agent

This guide will help you quickly get started with the new dashboard integration and AI agent features.

## 🚀 Installation

### 1. Install Dependencies

```bash
# Using UV (recommended - already done!)
uv pip install langgraph langchain langchain-openai langchain-core

# Or using pip
pip install langgraph langchain langchain-openai langchain-core
```

### 2. Configure Environment

Add your OpenAI API key to `.env`:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

## 🎯 Quick Test

### Test the Dashboard Client

```python
import asyncio
from src.utils.dashboard_client import get_dashboard_client

async def test_client():
    client = get_dashboard_client()
    
    # Fetch happiness data
    data = await client.fetch_chart_data("happiness")
    print("Chart data:", data)

asyncio.run(test_client())
```

### Test the AI Agent

```python
import asyncio
from src.analysis.langgraph_agent import get_dashboard_agent

async def test_agent():
    agent = get_dashboard_agent()
    
    # Ask a question
    result = await agent.analyze("How is team happiness?")
    print("AI Insights:", result["insights"])

asyncio.run(test_agent())
```

## 🌐 Using the API

### 1. Start the Server

```bash
uvicorn src.api.main:app --reload
```

Server will start at `http://localhost:8000`

### 2. Try the API

#### Get a Single Chart

```bash
curl http://localhost:8000/dashboard/charts/happiness
```

#### Get Multiple Charts

```bash
curl "http://localhost:8000/dashboard/charts?chart_names=happiness&chart_names=defect-rate-all"
```

#### Generate AI Insights

```bash
curl -X POST http://localhost:8000/dashboard/insights \
  -H "Content-Type: application/json" \
  -d '{"query": "How is team performance?", "include_chart_data": true}'
```

#### Chat with AI

```bash
curl -X POST "http://localhost:8000/dashboard/chat?message=What%27s%20the%20defect%20rate%3F"
```

#### List Available Charts

```bash
curl http://localhost:8000/dashboard/available-charts
```

## 📊 Interactive API Documentation

Visit these URLs after starting the server:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Run Tests

```bash
# Test dashboard client
pytest tests/test_dashboard_client.py -v

# Test AI agent
pytest tests/test_langgraph_agent.py -v

# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html
```

## 📖 Run Examples

```bash
# Run the demo script (shows 5 examples)
python examples/dashboard_ai_demo.py
```

## 💡 Common Use Cases

### Use Case 1: Get Team Happiness Insights

```python
import asyncio
from src.analysis.langgraph_agent import get_dashboard_agent

async def main():
    agent = get_dashboard_agent()
    result = await agent.analyze(
        "What's the current team happiness level and what factors might be affecting it?"
    )
    print(result["insights"])

asyncio.run(main())
```

### Use Case 2: Quality Analysis

```python
import asyncio
from src.utils.dashboard_client import get_dashboard_client
from src.analysis.langgraph_agent import get_dashboard_agent

async def quality_check():
    # Fetch quality metrics
    client = get_dashboard_client()
    charts = await client.fetch_multiple_charts([
        "defect-rate-all",
        "defect-rate-prod",
        "bugs-per-environment",
        "root-cause"
    ])
    
    # Get AI analysis
    agent = get_dashboard_agent()
    result = await agent.analyze(
        "Analyze the quality metrics. What are the main concerns and recommendations?"
    )
    
    print(result["insights"])

asyncio.run(quality_check())
```

### Use Case 3: Sprint Planning Data

```python
import asyncio
from src.utils.dashboard_client import get_dashboard_client

async def sprint_planning():
    client = get_dashboard_client()
    
    # Get planning-related charts
    data = await client.fetch_multiple_charts([
        "sp-distribution",
        "items-out-of-sprint",
        "velocity"
    ])
    
    # Use the data for sprint planning
    for chart_name, chart_data in data.items():
        print(f"\n{chart_name}:")
        print(chart_data)

asyncio.run(sprint_planning())
```

## 🎨 Frontend Integration

If you want to use this from your React frontend:

```typescript
// Fetch chart data
const response = await fetch('http://localhost:8000/dashboard/charts/happiness');
const data = await response.json();

// Get AI insights
const insightResponse = await fetch('http://localhost:8000/dashboard/insights', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'How is team performance?',
    include_chart_data: true
  })
});
const insights = await insightResponse.json();
console.log(insights.insights);
```

## 🔧 Troubleshooting

### Problem: "Module not found" errors

**Solution**: Make sure you're in the virtual environment and dependencies are installed:

```bash
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
uv pip install -e ".[dev]"
```

### Problem: "OpenAI API key not found"

**Solution**: Set your API key in `.env`:

```env
OPENAI_API_KEY=sk-your-key-here
```

### Problem: Token expired error

**Solution**: The client automatically refreshes tokens, but you can force a refresh:

```python
from src.utils.dashboard_client import get_dashboard_client
client = get_dashboard_client()
client.invalidate_token()
```

### Problem: Slow AI responses

**Solution**: Use a faster model or reduce temperature:

```python
from src.analysis.langgraph_agent import DashboardAnalysisAgent
agent = DashboardAnalysisAgent(
    model_name="gpt-3.5-turbo",  # Faster model
    temperature=0.3  # More focused responses
)
```

## 📚 Next Steps

1. **Read the full documentation**: `DASHBOARD_AI_IMPLEMENTATION.md`
2. **Review the examples**: `examples/dashboard_ai_demo.py`
3. **Explore the API**: http://localhost:8000/docs
4. **Run the tests**: `pytest tests/ -v`

## 🎉 You're Ready!

The dashboard integration and AI agent are now ready to use. Start the server and try making your first request!

```bash
# Start the server
uvicorn src.api.main:app --reload

# In another terminal, test it
curl http://localhost:8000/dashboard/health
```

For more details, see:
- `DASHBOARD_AI_IMPLEMENTATION.md` - Complete documentation
- `DASHBOARD_IMPLEMENTATION_SUMMARY.md` - Implementation summary
- `examples/dashboard_ai_demo.py` - Usage examples
