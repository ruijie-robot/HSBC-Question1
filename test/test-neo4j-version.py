from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import textwrap

# Langchain
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_openai import ChatOpenAI

# Warning control
import warnings
warnings.filterwarnings("ignore")


# Load from environment
load_dotenv('.env', override=True)
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def get_neo4j_version():
    with driver.session() as session:
        # 适用于 Neo4j 3.x
        result = session.run("""
            CALL dbms.components() 
            YIELD name, versions 
            WHERE name = 'Neo4j Kernel' 
            RETURN versions[0] AS version
        """)
        return result.single()["version"]

print("Neo4j 版本:", get_neo4j_version())


def get_labels():
    with driver.session() as session:
        result = session.run("""
            CALL db.schema.nodeTypeProperties() 
            YIELD nodeLabels, propertyName, propertyTypes
            RETURN nodeLabels, propertyName""")  # 返回所有标签
        return [record["nodeLabels"] for record in result]

labels = get_labels()
print("所有节点标签:", labels)


def get_visualization():
    with driver.session() as session:
        result = session.run("""CALL db.schema.visualization()""")  # 返回所有标签
        print(result)

get_visualization()

driver.close()