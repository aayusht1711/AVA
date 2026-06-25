"""
AVA Web Search Tool — Tavily API
"""

from tavily import AsyncTavilyClient
from core.config import settings


def get_tavily() -> AsyncTavilyClient:
    if not settings.TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not set in .env")
    return AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)


async def web_search(query: str, max_results: int = 5) -> dict:
    """
    Search the web using Tavily.
    Returns: { query, results: [{title, url, content, score}], answer }
    """
    client = get_tavily()

    response = await client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=True,
    )

    results = [
        {
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "content": r.get("content", "")[:500],  # trim long snippets
            "score":   round(r.get("score", 0), 3),
        }
        for r in response.get("results", [])
    ]

    return {
        "query":   query,
        "answer":  response.get("answer", ""),
        "results": results,
    }


def format_search_results(search_data: dict) -> str:
    """Format search results as readable text for the LLM."""
    lines = [f"**Search:** {search_data['query']}\n"]

    if search_data.get("answer"):
        lines.append(f"**Quick answer:** {search_data['answer']}\n")

    lines.append("**Sources:**")
    for i, r in enumerate(search_data["results"][:3], 1):
        lines.append(f"{i}. [{r['title']}]({r['url']})")
        lines.append(f"   {r['content'][:200]}...\n")

    return "\n".join(lines)
