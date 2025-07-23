from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from typing import TypedDict, Optional

from chatbot_with_kg import call_kg_chain
from chatbot_with_kg import get_response as get_response_kg
from chatbot_baseline import call_chain
from chatbot_baseline import get_response as get_response_baseline
from validator import get_active_llm_logger
from llm import get_qwen_llm

_ = load_dotenv()
qa_chain_with_kg = call_kg_chain()
qa_chain_with_baseline = call_chain()

active_llm_logger = get_active_llm_logger()

memory = SqliteSaver.from_conn_string(":memory:")

class AgentState(TypedDict):
    # 输入相关
    user_input: str  # 原始用户输入
    language: Optional[str]  # 检测到的语言 (zh-CN/zh-TW/en)
    intention: Optional[str]  # 识别的意图 (fee_query/other)
    # 最终响应
    response: Optional[str]  # 返回给用户的最终回复
    accuracy: Optional[str]  # 准确率 (low/medium/high)
    validation: Optional[bool]  # 格式和安全检查是否通过

qwen_llm = get_qwen_llm()


LANGUAGE_PROMPT = """You are a language detection assistant. Please identify the language of the following user input. Only output the language name, choosing from: English, Simplified Chinese, Traditional Chinese, or Other.

User input: {user_input}
"""

INTENTION_PROMPT = """You are an intention classification assistant. Please analyze the user's question and determine which of the following types it belongs to. Only output one of the following type codes:

- rate_query: Direct rate inquiry (e.g., "What is the fee for service X?")
- comparison: Comparison (e.g., "Which account is better, Y or Z?")
- eligibility: Eligibility verification for privileges (e.g., "Do I qualify for a fee waiver?")
- process: Process-related inquiry (e.g., "How do I apply for a paper statement fee waiver?")

User question: {user_input}

Output only the type code (rate_query, comparison, eligibility, or process). Do not explain your reasoning.
"""



GENERATE_PROMPT = """You are a helpful assistant. Please answer the user's question in the specified language.

Language: {language}
User question: {user_input}

Please provide a clear and concise answer in the specified language."""



############## NODE FUNCTIONS ##############
# (1) 语言检测 Agent
def language_node(state: AgentState) -> AgentState:
    # 使用qwen_llm判断语言
    prompt = LANGUAGE_PROMPT.format(user_input=state["user_input"])
    messages = [SystemMessage(content=prompt)]
    response = qwen_llm.invoke(messages)
    lang = response.content.strip()
    state["language"] = lang
    return state


# (2) 意图识别 Agent
def intention_node(state: AgentState) -> AgentState:
    # 使用qwen_llm来识别意图
    prompt = INTENTION_PROMPT.format(user_input=state["user_input"])
    messages = [SystemMessage(content=prompt)]
    response = qwen_llm.invoke(messages)
    intent = response.content.strip()
    state["intention"] = intent
    return state


# (6) 响应生成 Agent
def generation_node(state: AgentState) -> AgentState:
    # 根据意图选择不同的LLM调用方式
    if state.get("intention") == "other":
        # 使用baseline LLM，准确率为medium
        response = get_response_kg(qa_chain_with_kg, question=state["user_input"])
        state["accuracy"] = "medium"
    else:
        # 其他意图，使用知识图谱LLM，准确率为high
        response = get_response_baseline(qa_chain_with_baseline, question=state["user_input"])
        state["accuracy"] = "high"
    state["response"] = response
    return state


# (7) 验证 & 安全过滤 Agent
# def validate_node(state: AgentState) -> AgentState:
#     try:
#         active_llm_logger.log(
#         {"prompt": state["user_input"]}
#         )
#         active_llm_logger.log(
#             {"response": state["response"]}
#         )
#         state["validation"] = True
#     except LLMApplicationValidationError:
#         state["validation"] = False
#     return state
def validate_node(state: AgentState) -> AgentState:
    state["validation"] = True
    return state


# def should_continue(state):
#     if state["validation"] == False:
#         return END
#     return "reflect"

builder = StateGraph(AgentState)

builder.add_node("language", language_node)
builder.add_node("intention", intention_node)
builder.add_node("generation", generation_node)
builder.add_node("validation", validate_node)

builder.set_entry_point("language")


builder.add_edge("language", "intention")
builder.add_edge("intention", "generation")
builder.add_edge("generation", "validation")
builder.add_edge("validation", END)
# #TODO
# builder.add_conditional_edges(
#     "validation", 
#     should_continue, 
#     {END: END, "reflect": "reflect"}
# )

graph = builder.compile(checkpointer=memory)

# from IPython.display import Image

# Image(graph.get_graph().draw_png())

thread = {"configurable": {"thread_id": "1"}}
for s in graph.stream({'task': "what is the difference between langchain and langsmith", "max_revisions": 2,"revision_number": 1,}, thread):
    print(s)

