import os
import sys
import warnings

# Langchain
from langchain_community.graphs import Neo4jGraph
from dotenv import load_dotenv, find_dotenv


sys.path.append('../..')


_ = load_dotenv(find_dotenv()) 
load_dotenv('.env', override=True)
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'
# Warning control
warnings.filterwarnings("ignore")

def get_kg():
    kg = Neo4jGraph(
        url=NEO4J_URI, 
        username=NEO4J_USERNAME, 
        password=NEO4J_PASSWORD, 
        database=NEO4J_DATABASE
        )
    return kg