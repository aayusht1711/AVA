"""
AVA Researcher Agent
Uses Tavily to search the web and synthesize answers.
"""

from agents.router import complete, ModelChoice
from agents.prompts import RESEARCHER_SYSTEM_PROMPT
from tools.tavily_tool import web_search, format_search_results
import re


SEARCH_TRIGGERS = [
    r"\bsearch\b", r"\blook up\b", r"\bfind\b",
    r"\bwhat is\b", r"\bwho is\b", r"\bwhen did\b",
    r"\blatest\b", r"\bcurrent\b", r"\btoday\b",
    r"\bnews\b", r"\brecent\b", r"\b2024\b", r"\b2025\b",
]


def needs_search(message: str) -> bool:
    """Check if this message needs a web search."""
    lower = message.lower()
    return any(re.search(p, lower) for p in SEARCH_TRIGGERS)


async def research(
    query: str,
    conversation_history: list[dict] | None = None,
) -> dict:
    """
    Research a topic using Tavily + LLM synthesis.
    Returns: { answer, sources, raw_results }
    """
    # 1. Search
    search_data = await web_search(query, max_results=5)
    formatted = format_search_results(search_data)

    # 2. Synthesize with LLM
    messages = [
        {"role": "system", "content": RESEARCHER_SYSTEM_PROMPT},
    ]
    if conversation_history:
        messages.extend(conversation_history[-4:])  # last 2 turns for context

    messages.append({
        "role": "user",
        "content": (
            f"The user asked: {query}\n\n"
            f"Here are the search results:\n{formatted}\n\n"
            f"Synthesize a clear, helpful answer. Cite sources where relevant."
        ),
    })

    answer = await complete(messages, model=ModelChoice.GROQ)

    return {
        "answer":      answer,
        "sources":     [r["url"] for r in search_data["results"][:3]],
        "raw_results": search_data,
    }
