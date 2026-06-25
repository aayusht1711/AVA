"""
AVA File Agent
Processes uploaded PDFs, images (via Vision), CSVs, or code files.
"""

def needs_file(content: str) -> bool:
    lower = content.lower()
    return any(word in lower for word in ["read file", "process file", "what's in this image"])

async def handle_file(request: str, history: list[dict]) -> dict:
    # TODO: Implement Gemini 1.5 Flash Vision file reading
    return {"final_response": "I am reading the file. (File agent placeholder)"}
