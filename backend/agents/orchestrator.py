"""
AVA Orchestrator — LangGraph ReAct Loop
The brain. Routes every request to the right agent,
manages state, and streams responses back.
"""

from typing import TypedDict, Annotated, AsyncGenerator
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents.router import stream_completion
from agents.researcher import needs_search, research
from agents.coder import needs_code, generate_and_run_code
from agents.task import needs_task, handle_task
from agents.data import needs_data, handle_data
from agents.document import needs_document, handle_document
from agents.file_agent import needs_file, handle_file
from agents.prompts import AVA_SYSTEM_PROMPT
from memory.chroma import format_memories_for_context


# ── State ────────────────────────────────────────────────────────────

class AVAState(TypedDict):
    messages:        Annotated[list, add_messages]
    user_id:         str
    session_id:      str
    active_agent:    str           
    tool_result:     str
    memory_context:  str
    target_agent:    str


# ── Nodes ─────────────────────────────────────────────────────────────

async def router_node(state: AVAState) -> dict:
    """Decide which agent to use."""
    last = state["messages"][-1]
    content = last.content.lower() if hasattr(last, "content") else str(last).lower()

    target_agent = "synthesizer"
    
    # Priority routing based on keywords
    if any(kw in content for kw in ["code", "program", "debug"]):
        target_agent = "coder"
    elif any(kw in content for kw in ["search", "news", "what is"]):
        target_agent = "researcher"
    elif any(kw in content for kw in ["remind me", "task", "list"]):
        target_agent = "task"
    elif any(kw in content for kw in ["analyze", "csv", "plot"]):
        target_agent = "data"
    elif needs_document(content):
        target_agent = "document"
    elif needs_file(content):
        target_agent = "file"

    return {
        "target_agent": target_agent,
        "active_agent": "orchestrator",
    }


async def memory_node(state: AVAState) -> dict:
    """Load relevant memories for context."""
    last = state["messages"][-1]
    query = last.content if hasattr(last, "content") else str(last)

    memory_context = await format_memories_for_context(
        state["user_id"], query
    )
    return {"memory_context": memory_context}


async def researcher_node(state: AVAState) -> dict:
    last = state["messages"][-1]
    query = last.content if hasattr(last, "content") else str(last)
    history = _to_dict_history(state["messages"][:-1])
    result  = await research(query, history)
    return {"tool_result": result["answer"], "active_agent": "researcher"}


async def coder_node(state: AVAState) -> dict:
    last = state["messages"][-1]
    request = last.content if hasattr(last, "content") else str(last)
    history = _to_dict_history(state["messages"][:-1])
    result  = await generate_and_run_code(request, history)
    return {"tool_result": result["final_response"], "active_agent": "coder"}

async def task_node(state: AVAState) -> dict:
    last = state["messages"][-1]
    request = last.content if hasattr(last, "content") else str(last)
    history = _to_dict_history(state["messages"][:-1])
    result  = await handle_task(request, history)
    return {"tool_result": result["final_response"], "active_agent": "task"}

async def data_node(state: AVAState) -> dict:
    last = state["messages"][-1]
    request = last.content if hasattr(last, "content") else str(last)
    history = _to_dict_history(state["messages"][:-1])
    result  = await handle_data(request, history)
    return {"tool_result": result["final_response"], "active_agent": "data"}

async def document_node(state: AVAState) -> dict:
    last = state["messages"][-1]
    request = last.content if hasattr(last, "content") else str(last)
    history = _to_dict_history(state["messages"][:-1])
    result  = await handle_document(request, history)
    return {"tool_result": result["final_response"], "active_agent": "document"}

async def file_node(state: AVAState) -> dict:
    last = state["messages"][-1]
    request = last.content if hasattr(last, "content") else str(last)
    history = _to_dict_history(state["messages"][:-1])
    result  = await handle_file(request, history)
    return {"tool_result": result["final_response"], "active_agent": "file"}


async def synthesizer_node(state: AVAState) -> dict:
    """Build final response."""
    if state.get("tool_result"):
        response = state["tool_result"]
    else:
        history = _build_messages(state)
        chunks = []
        async for chunk in stream_completion(history):
            chunks.append(chunk)
        response = "".join(chunks)

    return {
        "messages":     [AIMessage(content=response)],
        "tool_result":  "",
        "active_agent": state.get("active_agent", "orchestrator"),
    }


# ── Routing edges ────────────────────────────────────────────────────

def route_after_router(state: AVAState) -> str:
    return state.get("target_agent", "synthesizer")


# ── Graph construction ───────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AVAState)

    graph.add_node("memory",      memory_node)
    graph.add_node("router",      router_node)
    graph.add_node("researcher",  researcher_node)
    graph.add_node("coder",       coder_node)
    graph.add_node("task",        task_node)
    graph.add_node("data",        data_node)
    graph.add_node("document",    document_node)
    graph.add_node("file",        file_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "memory")
    graph.add_edge("memory", "router")
    
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "researcher":  "researcher",
            "coder":       "coder",
            "task":        "task",
            "data":        "data",
            "document":    "document",
            "file":        "file",
            "synthesizer": "synthesizer",
        },
    )
    
    graph.add_edge("researcher",  "synthesizer")
    graph.add_edge("coder",       "synthesizer")
    graph.add_edge("task",        "synthesizer")
    graph.add_edge("data",        "synthesizer")
    graph.add_edge("document",    "synthesizer")
    graph.add_edge("file",        "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# Singleton compiled graph
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# ── Public API ────────────────────────────────────────────────────────

async def run_ava(
    user_message: str,
    user_id: str,
    session_id: str,
    history: list[dict] | None = None,
) -> AsyncGenerator[dict, None]:
    graph = get_graph()

    messages = []
    if history:
        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    initial_state: AVAState = {
        "messages":       messages,
        "user_id":        user_id,
        "session_id":     session_id,
        "active_agent":   "orchestrator",
        "tool_result":    "",
        "memory_context": "",
        "target_agent":   "synthesizer",
    }

    final_state = await graph.ainvoke(initial_state)

    agent = final_state.get("active_agent", "orchestrator")
    yield {"type": "agent", "agent": agent}

    last_ai = None
    for msg in reversed(final_state["messages"]):
        if hasattr(msg, "content") and isinstance(msg, AIMessage):
            last_ai = msg.content
            break

    if last_ai:
        chunk_size = 50
        for i in range(0, len(last_ai), chunk_size):
            yield {"type": "chunk", "content": last_ai[i:i+chunk_size]}

    yield {"type": "done", "agent": agent}


# ── Helpers ───────────────────────────────────────────────────────────

def _to_dict_history(messages: list) -> list[dict]:
    result = []
    for m in messages:
        if isinstance(m, HumanMessage):
            result.append({"role": "user",      "content": m.content})
        elif isinstance(m, AIMessage):
            result.append({"role": "assistant", "content": m.content})
        elif isinstance(m, SystemMessage):
            result.append({"role": "system",    "content": m.content})
    return result


def _build_messages(state: AVAState) -> list[dict]:
    system = AVA_SYSTEM_PROMPT
    if state.get("memory_context"):
        system = f"{system}\n\n{state['memory_context']}"

    msgs = [{"role": "system", "content": system}]
    msgs.extend(_to_dict_history(state["messages"]))
    return msgs
