from dotenv import load_dotenv
import os
import textwrap
import pandas as pd
from time import sleep

# Langchain
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import GraphCypherQAChain
from langchain_community.llms import Tongyi


import openai
import sys
sys.path.append('../..')

import panel as pn  # GUI
pn.extension()

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

# openai.api_key  = os.environ['OPENAI_API_KEY']
api_key = os.environ['DASHSCOPE_API_KEY']


import datetime
current_date = datetime.datetime.now().date()
llm_name = "qwen-plus"
print(llm_name)

qwen_llm = Tongyi(
    model_name="qwen-plus",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
)

# Warning control
import warnings
warnings.filterwarnings("ignore")


# Load from environment
load_dotenv('.env', override=True)
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'


kg = Neo4jGraph(
    url=NEO4J_URI, 
    username=NEO4J_USERNAME, 
    password=NEO4J_PASSWORD, 
    database=NEO4J_DATABASE
)

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


CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

cypherChain = GraphCypherQAChain.from_llm(
    llm=qwen_llm,#ChatOpenAI(model=llm_name, temperature=0),
    graph=kg,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    allow_dangerous_requests=True,  # 确认了解安全风险
)


# question = "What are charges of Bulk Cheque Deposit?"
# response = cypherChain.invoke({"query": question})
# print(response["result"])


question = "How can I waive charges of Bulk Cheque Deposit?"
response = cypherChain.invoke({"query": question})
print(response["result"])
print("stop")


# question = "How can I waive charges of Bulk Cash Deposit?"
# response = cypherChain.invoke({"query": question})
# print(response["result"])
# print("stop")
