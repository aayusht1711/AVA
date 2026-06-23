"""
AVA Data Agent
Statistical analysis and visualization. Detects chart type automatically and runs in E2B.
"""

from agents.coder import generate_and_run_code

def needs_data(content: str) -> bool:
    lower = content.lower()
    return any(word in lower for word in ["analyze", "csv", "plot", "graph", "chart", "dataset", "statistics"])

async def handle_data(request: str, history: list[dict]) -> dict:
    # We hijack the coder execution loop, but inject a data-specific prompt
    prompt = (
        f"You are the AVA Data Agent. The user wants data analysis or plotting: '{request}'.\n"
        "Write Python code using pandas, matplotlib, or seaborn. If generating a plot, "
        "save it as an image file so it can be viewed. Output only the code block.\n"
    )
    result = await generate_and_run_code(prompt, history, max_retries=2)
    return result
