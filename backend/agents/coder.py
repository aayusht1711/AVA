"""
AVA Coder Agent
Writes code → runs in E2B → auto-fixes errors (up to 3 retries).
"""

from agents.router import complete, ModelChoice
from agents.prompts import CODER_SYSTEM_PROMPT
from tools.e2b_tool import execute_code, format_execution_result
import re


CODE_TRIGGERS = [
    r"\bwrite\b.*\bcode\b", r"\bwrite\b.*\bscript\b",
    r"\bwrite\b.*\bfunction\b", r"\bdebug\b", r"\bfix\b.*\berror\b",
    r"\brun\b.*\bcode\b", r"\bexecute\b", r"\bpython\b",
    r"\bjavascript\b", r"\bimplement\b", r"\bprogram\b",
    r"\bscraper\b", r"\bautomation\b",
]


def needs_code(message: str) -> bool:
    lower = message.lower()
    return any(re.search(p, lower) for p in CODE_TRIGGERS)


def extract_code_block(text: str) -> tuple[str, str]:
    """
    Extract the first code block from markdown text.
    Returns (code, language).
    """
    pattern = r"```(\w+)?\n?([\s\S]*?)```"
    match = re.search(pattern, text)
    if match:
        lang = match.group(1) or "python"
        code = match.group(2).strip()
        return code, lang
    return "", "python"


async def generate_and_run_code(
    request: str,
    conversation_history: list[dict] | None = None,
    max_retries: int = 3,
) -> dict:
    """
    1. Ask LLM to write the code
    2. Execute in E2B sandbox
    3. If it fails, feed the error back and retry
    Returns: { code, language, result, iterations, final_response }
    """
    messages = [{"role": "system", "content": CODER_SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history[-4:])
    messages.append({"role": "user", "content": request})

    code = ""
    language = "python"
    result = {}
    iterations = 0

    for attempt in range(max_retries):
        iterations += 1

        # Generate code
        llm_response = await complete(messages, model=ModelChoice.GROQ)
        code, language = extract_code_block(llm_response)

        if not code:
            # LLM gave an explanation without code — return as-is
            return {
                "code": "", "language": language,
                "result": {}, "iterations": iterations,
                "final_response": llm_response,
                "executed": False,
            }

        # Execute in sandbox
        result = await execute_code(code, language=language)  # type: ignore

        if result["success"]:
            # Success — build final response
            final = (
                f"{llm_response}\n\n"
                f"{format_execution_result(result)}"
            )
            return {
                "code": code, "language": language,
                "result": result, "iterations": iterations,
                "final_response": final,
                "executed": True,
            }

        # Failed — feed error back for retry
        error_msg = result["error"] or result["stderr"]
        messages.append({"role": "assistant", "content": llm_response})
        messages.append({
            "role": "user",
            "content": (
                f"The code failed with this error:\n```\n{error_msg}\n```\n"
                f"Please fix the code and try again."
            ),
        })

    # All retries exhausted
    final = (
        f"I tried {max_retries} times but couldn't fix the error:\n"
        f"```\n{result.get('error', 'Unknown error')}\n```\n"
        f"Here's the last version of the code:\n"
        f"```{language}\n{code}\n```"
    )
    return {
        "code": code, "language": language,
        "result": result, "iterations": iterations,
        "final_response": final,
        "executed": False,
    }
