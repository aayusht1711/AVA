"""
AVA Document Agent
Generates structured PDFs from natural language.
"""

def needs_document(content: str) -> bool:
    lower = content.lower()
    return any(word in lower for word in ["generate pdf", "create pdf", "report"])

async def handle_document(request: str, history: list[dict]) -> dict:
    # TODO: Implement ReportLab PDF generation
    return {"final_response": "I am generating the PDF. (Document agent placeholder)"}
