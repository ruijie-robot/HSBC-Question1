import sys

# Langchain
from langchain.chains import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate
from dotenv import load_dotenv, find_dotenv

from llm import get_qwen_llm
from kg import get_kg

sys.path.append('../..')

def create_kg_chain():
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
    response = cypherChain.invoke({"query": question})
    return response["result"]

def test_chatbot_with_kg(cypherChain):
    question1 = "What are charges of Bulk Cheque Deposit?"
    question2 = "How can I waive charges of Bulk Cheque Deposit?"
    question3 = "How can I waive charges of Bulk Cash Deposit?"

    response1 = get_response(cypherChain, question1)
    response2 = get_response(cypherChain, question2)
    response3 = get_response(cypherChain, question3)
    print(response1)
    print(response2)
    print(response3)

def main():
    cypherChain = create_kg_chain()

    test_chatbot_with_kg(cypherChain)

if __name__ == "__main__":
    main()