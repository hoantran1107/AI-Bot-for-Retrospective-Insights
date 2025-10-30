"""
Example script demonstrating dashboard integration and AI agent usage.

This script shows how to:
1. Fetch dashboard data from N8N webhooks
2. Use the AI agent for intelligent analysis
3. Generate insights and recommendations
"""

import asyncio
import json
from src.utils.dashboard_client import get_dashboard_client
from src.analysis.langgraph_agent import get_dashboard_agent


async def example_1_fetch_single_chart():
    """Example 1: Fetch data for a single chart."""
    print("\n" + "=" * 60)
    print("Example 1: Fetch Single Chart Data")
    print("=" * 60)

    client = get_dashboard_client()

    # Fetch happiness data
    print("\nFetching team happiness data...")
    data = await client.fetch_chart_data("happiness")

    print(f"\nChart Data:")
    print(json.dumps(data, indent=2)[:500])  # First 500 chars
    print("\n✓ Successfully fetched happiness chart data")


async def example_2_fetch_multiple_charts():
    """Example 2: Fetch data for multiple charts."""
    print("\n" + "=" * 60)
    print("Example 2: Fetch Multiple Charts")
    print("=" * 60)

    client = get_dashboard_client()

    # Fetch multiple charts
    chart_names = ["happiness", "defect-rate-all", "review-time"]
    print(f"\nFetching {len(chart_names)} charts: {', '.join(chart_names)}")

    charts = await client.fetch_multiple_charts(chart_names)

    print(f"\nFetched {len(charts)} charts successfully:")
    for chart_name, data in charts.items():
        if "error" in data:
            print(f"  ✗ {chart_name}: Error - {data['error']}")
        else:
            print(f"  ✓ {chart_name}: OK")


async def example_3_ai_analysis():
    """Example 3: Use AI agent for intelligent analysis."""
    print("\n" + "=" * 60)
    print("Example 3: AI-Powered Analysis")
    print("=" * 60)

    agent = get_dashboard_agent()

    # Analyze team happiness
    query = "How is team happiness trending? What factors might be contributing?"
    print(f"\nQuery: {query}")
    print("\nAnalyzing... (this may take a few seconds)")

    result = await agent.analyze(query)

    if result["success"]:
        print(f"\n{'=' * 60}")
        print("AI INSIGHTS")
        print("=" * 60)
        print(result["insights"])
        print("\n" + "=" * 60)

        print(f"\nRelevant Charts Analyzed:")
        relevant_charts = result["analysis"].get("relevant_charts", [])
        for chart in relevant_charts:
            print(f"  • {chart}")

        print(f"\nTrends Detected:")
        trends = result["analysis"].get("trends", [])
        if trends:
            for trend in trends:
                print(
                    f"  • {trend['chart']}: {trend['direction']} by {trend['change']}"
                )
        else:
            print("  • No significant trends detected")
    else:
        print(f"\n✗ Analysis failed: {result.get('error', 'Unknown error')}")


async def example_4_simple_chat():
    """Example 4: Simple chat interface with AI agent."""
    print("\n" + "=" * 60)
    print("Example 4: Chat with AI Agent")
    print("=" * 60)

    agent = get_dashboard_agent()

    questions = [
        "What's the current defect rate?",
        "Are there any quality concerns?",
        "How much time is spent on code review?",
    ]

    for question in questions:
        print(f"\n👤 You: {question}")
        response = await agent.chat(question)
        print(f"🤖 Agent: {response[:200]}...")  # First 200 chars


async def example_5_comprehensive_report():
    """Example 5: Generate comprehensive team health report."""
    print("\n" + "=" * 60)
    print("Example 5: Comprehensive Team Health Report")
    print("=" * 60)

    agent = get_dashboard_agent()
    client = get_dashboard_client()

    # Fetch key metrics
    print("\nFetching key team metrics...")
    key_charts = [
        "happiness",
        "defect-rate-all",
        "review-time",
        "coding-time",
        "items-out-of-sprint",
    ]

    charts = await client.fetch_multiple_charts(key_charts)

    # Generate comprehensive analysis
    query = """
    Based on the available dashboard data, provide a comprehensive team health report.
    Include:
    1. Overall team health score
    2. Key strengths and concerns
    3. Trend analysis
    4. Top 3 recommendations for improvement
    """

    print("\nGenerating comprehensive analysis...")
    result = await agent.analyze(query)

    if result["success"]:
        print(f"\n{'=' * 60}")
        print("COMPREHENSIVE TEAM HEALTH REPORT")
        print("=" * 60)
        print(result["insights"])
        print("\n" + "=" * 60)
    else:
        print(f"\n✗ Report generation failed: {result.get('error', 'Unknown error')}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("DASHBOARD INTEGRATION & AI AGENT EXAMPLES")
    print("=" * 60)
    print("\nThis script demonstrates the dashboard integration")
    print("and AI agent capabilities.")
    print("\nNote: Requires valid OpenAI API key and network access")
    print("to N8N webhooks.")

    try:
        # Run examples
        await example_1_fetch_single_chart()
        await example_2_fetch_multiple_charts()
        await example_3_ai_analysis()
        await example_4_simple_chat()
        await example_5_comprehensive_report()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("\nPlease check:")
        print("  1. OpenAI API key is set in .env")
        print("  2. Network access to N8N webhooks")
        print("  3. All dependencies are installed")


if __name__ == "__main__":
    asyncio.run(main())
