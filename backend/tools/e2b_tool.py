"""
AVA Code Execution Tool — E2B Isolated Sandbox
NEVER use exec() or subprocess on the host machine.
All code runs in E2B's cloud sandbox.
"""

from e2b_code_interpreter import AsyncSandbox
from core.config import settings
from typing import Literal


CodeLanguage = Literal["python", "javascript"]


async def execute_code(
    code: str,
    language: CodeLanguage = "python",
    timeout: int = 30,
) -> dict:
    """
    Execute code in E2B sandbox.
    Returns: { success, stdout, stderr, error, output_files }
    """
    if not settings.E2B_API_KEY:
        return {
            "success": False,
            "stdout": "",
            "stderr": "E2B_API_KEY not configured.",
            "error": "E2B_API_KEY not set in .env",
            "output_files": [],
        }

    try:
        async with AsyncSandbox(api_key=settings.E2B_API_KEY) as sandbox:
            if language == "python":
                execution = await sandbox.run_code(code, timeout=timeout)
            else:
                # JavaScript via Node
                execution = await sandbox.run_code(
                    f"const result = eval(`{code}`); console.log(result)",
                    language="js",
                    timeout=timeout,
                )

            stdout = "\n".join(str(r) for r in execution.logs.stdout) if execution.logs.stdout else ""
            stderr = "\n".join(str(r) for r in execution.logs.stderr) if execution.logs.stderr else ""
            error  = str(execution.error) if execution.error else ""

            return {
                "success":      not execution.error,
                "stdout":       stdout,
                "stderr":       stderr,
                "error":        error,
                "output_files": [],
            }

    except Exception as e:
        return {
            "success":      False,
            "stdout":       "",
            "stderr":       "",
            "error":        f"Sandbox error: {str(e)}",
            "output_files": [],
        }


def format_execution_result(result: dict) -> str:
    """Format execution result as readable text for the LLM."""
    if result["success"]:
        out = result["stdout"] or "(no output)"
        return f"✅ **Executed successfully**\n```\n{out}\n```"
    else:
        err = result["error"] or result["stderr"] or "Unknown error"
        return f"❌ **Execution failed**\n```\n{err}\n```"
