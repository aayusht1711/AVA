"""
AVA File Agent
Handles local filesystem operations: list, read, write, create directories.
"""

import os
import json
from agents.router import complete, ModelChoice

def needs_file(content: str) -> bool:
    lower = content.lower()
    return any(word in lower for word in ["read file", "write file", "local file", "directory", "folder"])

async def handle_file(request: str, history: list[dict]) -> dict:
    # 1. Ask the LLM what operation it wants to do
    system_prompt = (
        "You are the AVA File Agent. You have access to the local filesystem. "
        "Available operations:\n"
        "1. list_dir: {'op': 'list_dir', 'path': '...'}\n"
        "2. read_file: {'op': 'read_file', 'path': '...'}\n"
        "3. write_file: {'op': 'write_file', 'path': '...', 'content': '...'}\n"
        "Output ONLY valid JSON representing the operation, or a normal text response if the user query is satisfied."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
    ] + history + [{"role": "user", "content": request}]
    
    response = await complete(messages, model=ModelChoice.GROQ)
    
    try:
        data = json.loads(response)
        op = data.get("op")
        path = data.get("path", "")
        
        # Security: Prevent escaping the workspace directory in a real app, but for personal Jarvis we allow it.
        # But we default to resolving absolute paths.
        abs_path = os.path.abspath(path)
        
        result_text = ""
        if op == "list_dir":
            try:
                items = os.listdir(abs_path)
                result_text = f"Directory contents of {abs_path}: " + ", ".join(items)
            except Exception as e:
                result_text = f"Error listing directory: {e}"
        elif op == "read_file":
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
                result_text = f"File contents of {abs_path}:\n\n{content}"
            except Exception as e:
                result_text = f"Error reading file: {e}"
        elif op == "write_file":
            try:
                content = data.get("content", "")
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(content)
                result_text = f"Successfully wrote to {abs_path}"
            except Exception as e:
                result_text = f"Error writing file: {e}"
        else:
            result_text = f"Unknown operation: {op}"
            
        # Re-evaluate with the result
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "system", "content": f"Operation Result:\n{result_text}"})
        final_response = await complete(messages, model=ModelChoice.GROQ)
        return {"final_response": final_response}

    except json.JSONDecodeError:
        # It's a normal text response
        return {"final_response": response}
