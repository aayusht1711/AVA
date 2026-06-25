"""
AVA Data Agent
Statistical analysis and visualization. Detects chart type automatically.
"""

def needs_data(content: str) -> bool:
    lower = content.lower()
    return any(word in lower for word in ["analyze", "csv", "plot"])

async def handle_data(request: str, history: list[dict]) -> dict:
    # TODO: Implement Pandas data analysis and charting
    return {"final_response": "I am analyzing the data for you. (Data agent placeholder)"}
