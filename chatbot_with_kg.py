import os
import sys
import warnings

# Langchain
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_community.llms import Tongyi
from langchain.chains import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate
from dotenv import load_dotenv, find_dotenv


sys.path.append('../..')


_ = load_dotenv(find_dotenv()) 
load_dotenv('.env', override=True)
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'
api_key = os.environ['DASHSCOPE_API_KEY']
# Warning control
warnings.filterwarnings("ignore")

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

    qwen_llm = Tongyi(
    model_name="qwen-plus",
    dashscope_api_key=api_key
    )

    kg = Neo4jGraph(
    url=NEO4J_URI, 
    username=NEO4J_USERNAME, 
    password=NEO4J_PASSWORD, 
    database=NEO4J_DATABASE
    )

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

def test_chatbot_with_kg(cypherChain):
    question1 = "What are charges of Bulk Cheque Deposit?"
    question2 = "How can I waive charges of Bulk Cheque Deposit?"
    question3 = "How can I waive charges of Bulk Cash Deposit?"
    response = cypherChain.invoke({"query": question1})
    print(response["result"])


def main():
    cypherChain = create_kg_chain()

    test_chatbot_with_kg(cypherChain)

if __name__ == "__main__":
    main()