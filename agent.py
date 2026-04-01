"""
AI Code Debugging Agent using LangGraph
Supports: Bug detection, Auto-fix, Multi-language, Chat interface
Using: Google Gemini (Free API)
"""

from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI   # ✅ CHANGED
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv                              # ✅ ADDED
from langchain_groq import ChatGroq
import re
import os

# ✅ ADDED: Load API key from .env file
load_dotenv()

# ── LLM Setup ─────────────────────────────────────────────────────────────────

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── Agent State ───────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]   # Full chat history
    code: str                                  # The code being debugged
    language: str                              # Detected/specified language
    bugs: List[str]                            # List of detected bugs
    fixed_code: Optional[str]                  # Auto-fixed version of code
    explanation: str                           # Human-readable explanation
    action: str                                # Current node action


# ── Node 1: Detect Language ────────────────────────────────────────────────────
def detect_language(state: AgentState) -> AgentState:
    """Auto-detect programming language from code snippet."""
    code = state["code"]

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            "You are a programming language detector. "
            "Reply with ONLY the language name, nothing else. "
            "Examples: Python, JavaScript, TypeScript, Java, C++, Go, Rust, Ruby, PHP, Swift"
        )),
        HumanMessage(content=f"Detect the programming language of this code:\n\n{code}")
    ])

    response = llm.invoke(prompt.format_messages())
    language = response.content.strip()

    return {**state, "language": language, "action": "detect_language"}


# ── Node 2: Detect Bugs ────────────────────────────────────────────────────────
def detect_bugs(state: AgentState) -> AgentState:
    """Analyze code and identify all bugs with line references."""
    code = state["code"]
    language = state["language"]

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            f"You are an expert {language} debugger. "
            "Analyze the code for bugs, errors, and issues. "
            "List each bug on a new line starting with '- '. "
            "Include: line number if possible, bug type, and brief description. "
            "Be specific and technical."
        )),
        HumanMessage(content=f"Find all bugs in this {language} code:\n\n```{language}\n{code}\n```")
    ])

    response = llm.invoke(prompt.format_messages())
    raw = response.content.strip()

    # Parse bullet-point bugs into a list
    bugs = [
        line.lstrip("- ").strip()
        for line in raw.splitlines()
        if line.strip().startswith("-")
    ]
    if not bugs:
        bugs = [raw]  # fallback: treat whole response as one bug block

    return {**state, "bugs": bugs, "action": "detect_bugs"}


# ── Node 3: Explain Bugs ───────────────────────────────────────────────────────
def explain_bugs(state: AgentState) -> AgentState:
    """Generate a clear, educational explanation of each bug."""
    bugs = state["bugs"]
    language = state["language"]
    code = state["code"]

    if not bugs or bugs == ["No bugs found."]:
        explanation = "✅ No bugs detected! Your code looks clean."
        return {**state, "explanation": explanation, "action": "explain_bugs"}

    bug_list = "\n".join(f"- {b}" for b in bugs)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            f"You are a friendly {language} coding mentor. "
            "Explain each bug clearly for an intermediate developer. "
            "For each bug: explain WHY it's a bug, what could go wrong, and how to think about it. "
            "Use simple language with technical accuracy."
        )),
        HumanMessage(content=(
            f"Explain these bugs found in the {language} code:\n\n"
            f"Code:\n```{language}\n{code}\n```\n\n"
            f"Bugs found:\n{bug_list}"
        ))
    ])

    response = llm.invoke(prompt.format_messages())
    return {**state, "explanation": response.content.strip(), "action": "explain_bugs"}


# ── Node 4: Auto-Fix Code ──────────────────────────────────────────────────────
def fix_code(state: AgentState) -> AgentState:
    """Generate a corrected version of the code with all bugs fixed."""
    code = state["code"]
    bugs = state["bugs"]
    language = state["language"]

    bug_list = "\n".join(f"- {b}" for b in bugs)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            f"You are an expert {language} developer. "
            "Fix all bugs in the provided code. "
            "Return ONLY the corrected code inside a code block. "
            "Do not include any explanation — just the fixed code."
        )),
        HumanMessage(content=(
            f"Fix all bugs in this {language} code:\n\n"
            f"```{language}\n{code}\n```\n\n"
            f"Known bugs:\n{bug_list}"
        ))
    ])

    response = llm.invoke(prompt.format_messages())
    raw = response.content.strip()

    # Extract code from markdown code block if present
    match = re.search(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
    fixed = match.group(1).strip() if match else raw

    return {**state, "fixed_code": fixed, "action": "fix_code"}


# ── Node 5: Chat Response ──────────────────────────────────────────────────────
def chat_response(state: AgentState) -> AgentState:
    """Generate a conversational chat reply summarizing the debug session."""
    bugs = state["bugs"]
    explanation = state["explanation"]
    fixed_code = state.get("fixed_code", "")
    language = state["language"]

    bug_count = len(bugs)
    summary = (
        f"✅ No bugs found in your {language} code!"
        if not bugs or bugs == ["No bugs found."]
        else f"🐛 Found {bug_count} bug(s) in your {language} code. Here's what I found and fixed:"
    )

    chat_msg = AIMessage(content=(
        f"{summary}\n\n"
        f"**Explanation:**\n{explanation}\n\n"
        + (f"**Fixed Code:**\n```{language}\n{fixed_code}\n```" if fixed_code else "")
    ))

    return {**state, "messages": state["messages"] + [chat_msg], "action": "chat_response"}


# ── Build LangGraph ────────────────────────────────────────────────────────────
def build_debug_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("detect_language", detect_language)
    graph.add_node("detect_bugs",     detect_bugs)
    graph.add_node("explain_bugs",    explain_bugs)
    graph.add_node("fix_code",        fix_code)
    graph.add_node("chat_response",   chat_response)

    graph.set_entry_point("detect_language")
    graph.add_edge("detect_language", "detect_bugs")
    graph.add_edge("detect_bugs",     "explain_bugs")
    graph.add_edge("explain_bugs",    "fix_code")
    graph.add_edge("fix_code",        "chat_response")
    graph.add_edge("chat_response",   END)

    return graph.compile()


# ── Public API ────────────────────────────────────────────────────────────────
debug_agent = build_debug_graph()


def run_debug_agent(code: str, chat_history: list = None) -> dict:
    """
    Run the full debugging pipeline on a code snippet.

    Args:
        code: The source code to debug
        chat_history: Optional prior messages for multi-turn context

    Returns:
        dict with keys: language, bugs, explanation, fixed_code, messages
    """
    initial_state: AgentState = {
        "messages":    chat_history or [HumanMessage(content=f"Debug this code:\n{code}")],
        "code":        code,
        "language":    "",
        "bugs":        [],
        "fixed_code":  None,
        "explanation": "",
        "action":      "",
    }

    result = debug_agent.invoke(initial_state)
    return {
        "language":    result["language"],
        "bugs":        result["bugs"],
        "explanation": result["explanation"],
        "fixed_code":  result["fixed_code"],
        "messages":    result["messages"],
    }


# ── CLI Quick Test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    average = total / len(numbers)  # Bug: ZeroDivisionError if empty list
    return average

nums = [1, 2, 3, 4, 5
print(calculate_average(nums))  # Bug: missing closing bracket
print(calculate_average([]))    # Bug: will crash
"""

    print("🤖 AI Code Debugging Agent\n" + "="*50)
    result = run_debug_agent(sample_code)

    print(f"📌 Language: {result['language']}")
    print(f"\n🐛 Bugs Found ({len(result['bugs'])}):")
    for i, bug in enumerate(result['bugs'], 1):
        print(f"  {i}. {bug}")

    print(f"\n📖 Explanation:\n{result['explanation']}")
    print(f"\n✅ Fixed Code:\n{result['fixed_code']}")
