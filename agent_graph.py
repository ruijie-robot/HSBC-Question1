from typing import TypedDict, Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage

from chatbot_with_kg import call_kg_chain, get_response as get_response_kg
from chatbot_baseline import call_chain, get_response as get_response_baseline
from llm import get_qwen_llm
from validator_toxicity import is_toxicity
from validator_refusal import is_refusal
# from validator_data_leakage import is_data_leakage

_ = load_dotenv()
qa_chain_with_kg = call_kg_chain()
qa_chain_with_baseline = call_chain()


memory = SqliteSaver.from_conn_string(":memory:")

class AgentState(TypedDict):
    # 输入相关
    user_input: str  # 原始用户输入
    language: Optional[str]  # 检测到的语言 (zh-CN/zh-TW/en)
    intention: Optional[str]  # 识别的意图 (fee_query/other)
    # 最终响应
    response: Optional[str]  # 返回给用户的最终回复
    accuracy: Optional[str]  # 准确率 (low/medium/high)
    prior_validation: Optional[bool]  # 格式和安全检查是否通过
    post_validation: Optional[bool]  # 格式和安全检查是否通过

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
    messages = [HumanMessage(content=prompt)]
    response = qwen_llm.invoke(messages)
    lang = response.strip()
    state["language"] = lang
    return state


# (2) 意图识别 Agent
def intention_node(state: AgentState) -> AgentState:
    # 使用qwen_llm来识别意图
    prompt = INTENTION_PROMPT.format(user_input=state["user_input"])
    messages = [ChatMessage(role="assistant", content=prompt)]
    response = qwen_llm.invoke(messages)
    intent = response.strip()
    state["intention"] = intent
    return state


# (3) 响应生成 Agent
def generation_node(state: AgentState) -> AgentState:
    # 根据意图选择不同的LLM调用方式
    prompt = GENERATE_PROMPT.format(language=state["language"], user_input=state["user_input"])
    messages = ChatMessage(role="assistant", content=prompt)
    if state.get("intention") == "other":
        # 使用baseline LLM，准确率为medium
        response = get_response_baseline(qa_chain_with_baseline, question=messages)
        state["accuracy"] = "medium"
    else:
        # 其他意图，使用知识图谱LLM，准确率为high
        response = get_response_kg(qa_chain_with_kg, question=messages)
        state["accuracy"] = "high"
    state["response"] = response
    return state


# (4) 验证 & 安全过滤 Agent
def prior_validation_node(state: AgentState) -> AgentState:
    toxicity_flag = is_toxicity(state["user_input"])
    if toxicity_flag:
        state["prior_validation"] = False
    else:
        state["prior_validation"] = True
    return state

def post_validation_node(state: AgentState) -> AgentState:
    toxicity_flag = is_toxicity(state["response"])
    refusal_flag = is_refusal(state["response"])
    if toxicity_flag or refusal_flag:
        state["post_validation"] = False
        print(f"toxicity_flag = {toxicity_flag}, refusal_flag={refusal_flag}")
        print("Sorry, I can't respond to that request.")
    else:
        state["post_validation"] = True
        print(state["response"])
    return state


builder = StateGraph(AgentState)

builder.add_node("prior_validation", prior_validation_node)
builder.add_node("language", language_node)
builder.add_node("intention", intention_node)
builder.add_node("generation", generation_node)
builder.add_node("post_validation", post_validation_node)

builder.set_entry_point("prior_validation")
builder.add_edge("language", "intention")
builder.add_edge("intention", "generation")
builder.add_edge("generation", "post_validation")
builder.add_edge("post_validation", END)

def should_continue(state):
    if state["prior_validation"] == False:
        print("Sorry, I can't respond to that request.")
        return END
    return "language"

builder.add_conditional_edges(
    "prior_validation", 
    should_continue, 
    {END: END, "language": "language"}
)

# graph = builder.compile(checkpointer=memory)
graph = builder.compile()


question1 = "如何豁免大支票存款的手续费?"
question2 = "这个银行的服务烂透了，该被炸掉！"
question3 = "今天天气不错哦"
thread = {"configurable": {"thread_id": "1"}}
for s in graph.stream({'user_input': question1, "max_revisions": 2,"revision_number": 1,}, thread):
    print(s)

