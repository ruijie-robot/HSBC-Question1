import sys

# Langchain
from langchain.chains import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate
from dotenv import load_dotenv, find_dotenv

from llm import get_qwen_llm
from kg import get_kg
from questions import get_question_library

sys.path.append('../..')

def call_kg_chain():
    CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to 
    query a graph database.
    Instructions:
    Use only the provided relationship types and properties in the 
    schema. Do not use any other relationship types or properties that 
    are not provided.
    Schema:
    {schema}
    Note: Do not include any explanations or apologies in your responses.
    Do not respond to any questions that might ask anything else than 
    for you to construct a Cypher statement.
    Do not include any text except the generated Cypher statement.
    Examples: Here are a few examples of generated Cypher 
    statements for particular questions:

    # What are charges of Bulk Cheque Deposit?
    MATCH (service:SERVICE {{name: "Bulk Cheque Deposit"}})-->(fee_rule:FEE_RULE)
        OPTIONAL MATCH (fee_rule)-[:HAS_FOOTNOTE]->(footnote:FOOTNOTE)
    RETURN service.name, fee_rule.description, footnote.note

    # How can I waive charges of Bulk Cash Deposit?
    MATCH (service:SERVICE {{name: "Bulk Cash Deposit"}})-->(fee_rule:FEE_RULE)
        OPTIONAL MATCH (fee_rule)-[:HAS_FOOTNOTE]->(footnote:FOOTNOTE)
    RETURN service.name, fee_rule.description, footnote.note


    The question is:
    {question}"""

    qwen_llm = get_qwen_llm()
    kg = get_kg()

    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], 
        template=CYPHER_GENERATION_TEMPLATE
    )

    cypherChain = GraphCypherQAChain.from_llm(
        llm=qwen_llm,
        graph=kg,
        verbose=True,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
        allow_dangerous_requests=True,  # 确认了解安全风险
    )

    return cypherChain

def get_response(cypherChain, question):
    try:
        response = cypherChain.invoke({"query": question})
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry,I donnot know."
    return response["result"]

def test_chatbot_with_kg(cypherChain):
    questions = get_question_library()
    for question in questions:
        response = get_response(cypherChain, question)
        print(f"question: {question}\nresponse: {response}")

def main():
    cypherChain = call_kg_chain()
    test_chatbot_with_kg(cypherChain)
    print("Done")

if __name__ == "__main__":
    main()