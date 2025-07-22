from dotenv import load_dotenv

_ = load_dotenv()

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage

memory = SqliteSaver.from_conn_string(":memory:")

class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revisions: int

from llm import get_qwen_llm
model = get_qwen_llm()

CLASSIFICATION_PROMPT = """You are an intelligent assistant tasked with classifying user questions. Please follow these steps:

1. First, identify the language of the user's question (choose only one from the following options):
- English
- Simplified Chinese
- Traditional Chinese
- Other

2. Then, determine which of the following categories the user's question belongs to (choose only one):
- Direct rate inquiry (e.g., "What is the fee for service X?")
- Comparison (e.g., "Which account is better, Y or Z?")
- Eligibility verification for privileges (e.g., "Do I qualify for a fee waiver?")
- Process-related inquiry (e.g., "How do I apply for a paper statement fee waiver?")
- Other

Please output your judgment in the following JSON format:
{{
  "language": "your judgment(e.g. Simplified Chinese)",
  "question_type": "your judgment(e.g. Comparison)"
}}

User question: {question}
"""


GENERATE_PROMPT = """You are an intelligent assistant. Answer the user's question according to the specified language and question_type, following these rules:

1. Always respond in the specified language (e.g., English, Simplified Chinese, Traditional Chinese, etc.).
2. If question_type is "Direct rate inquiry", use api-kg to answer.
3. For all other question types, use api-baseline to answer.

Input:
language: {language}
question_type: {question_type}
user_question: {question}

Please output only the final answer in the specified language. Do not explain your reasoning or mention which API you used.
"""



from langchain_core.pydantic_v1 import BaseModel

class Queries(BaseModel):
    queries: List[str]

# from tavily import TavilyClient
# import os
# tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def classification_node(state: AgentState):
    messages = [
        SystemMessage(content=CLASSIFICATION_PROMPT), 
        HumanMessage(content=state['task'])
    ]
    response = model.invoke(messages)
    return {"plan": response.content}

# def research_plan_node(state: AgentState):
#     queries = model.with_structured_output(Queries).invoke([
#         SystemMessage(content=RESEARCH_PLAN_PROMPT),
#         HumanMessage(content=state['task'])
#     ])
#     content = state['content'] or []
#     for q in queries.queries:
#         response = tavily.search(query=q, max_results=2)
#         for r in response['results']:
#             content.append(r['content'])
#     return {"content": content}

def generation_node(state: AgentState):
    content = "\n\n".join(state['content'] or [])
    user_message = HumanMessage(
        content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}")
    messages = [
        SystemMessage(
            content=GENERATE_PROMPT.format(content=content)
        ),
        user_message
        ]
    response = model.invoke(messages)
    return {
        "draft": response.content, 
        "revision_number": state.get("revision_number", 1) + 1
    }

# def reflection_node(state: AgentState):
#     messages = [
#         SystemMessage(content=REFLECTION_PROMPT), 
#         HumanMessage(content=state['draft'])
#     ]
#     response = model.invoke(messages)
#     return {"critique": response.content}

# def research_critique_node(state: AgentState):
#     queries = model.with_structured_output(Queries).invoke([
#         SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
#         HumanMessage(content=state['critique'])
#     ])
#     content = state['content'] or []
#     for q in queries.queries:
#         response = tavily.search(query=q, max_results=2)
#         for r in response['results']:
#             content.append(r['content'])
#     return {"content": content}

def should_continue(state):
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "reflect"

builder = StateGraph(AgentState)

builder.add_node("classification", classification_node)
builder.add_node("generate", generation_node)
# builder.add_node("reflect", reflection_node)
# builder.add_node("research_plan", research_plan_node)
# builder.add_node("research_critique", research_critique_node)

builder.set_entry_point("classification")

builder.add_conditional_edges(
    "generate", 
    should_continue, 
    {END: END, "reflect": "reflect"}
)

builder.add_edge("classification", "generate")

graph = builder.compile(checkpointer=memory)

# from IPython.display import Image

# Image(graph.get_graph().draw_png())

thread = {"configurable": {"thread_id": "1"}}
for s in graph.stream({'task': "what is the difference between langchain and langsmith", "max_revisions": 2,"revision_number": 1,}, thread):
    print(s)

