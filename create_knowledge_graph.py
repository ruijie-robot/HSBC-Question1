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

# Warning control
import warnings
warnings.filterwarnings("ignore")


# Load from environment
load_dotenv('.env', override=True)
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'

# Global constants
# VECTOR_INDEX_NAME = 'form_10k_chunks'
# VECTOR_NODE_LABEL = 'Chunk'
# VECTOR_SOURCE_PROPERTY = 'text'
# VECTOR_EMBEDDING_PROPERTY = 'textEmbedding'


kg = Neo4jGraph(
    url=NEO4J_URI, 
    username=NEO4J_USERNAME, 
    password=NEO4J_PASSWORD, 
    database=NEO4J_DATABASE
)


### 是否需要重新创建一个index
cards_df = pd.read_csv('./data/cards.csv', header=0)
services_df = pd.read_csv('./data/services.csv', header=0)
footnotes_df = pd.read_csv('./data/footnotes.csv', header=0)
fee_rules_df = pd.read_csv('./data/fee_rules.csv', header=0)
cards_list_of_dicts = cards_df.to_dict(orient='records')
services_list_of_dicts = services_df.to_dict(orient='records')
footnotes_list_of_dicts = footnotes_df.to_dict(orient='records')
fee_rules_list_of_dicts = fee_rules_df.to_dict(orient='records')



### Create graph nodes using text chunks
def create_node(kg, node_list_of_dicts, query):
    ### Loop through and create nodes for all cards
    node_count = 0
    for node_dict in node_list_of_dicts:
        # print(f"Creating `:Chunk` node for chunk ID {chunk['chunkId']}")
        kg.query(query, 
                params={
                    'params': node_dict
                })
        node_count += 1
    print(f"Created {node_count} nodes")


merge_card_node_query = """
MERGE(card:CARD {id: $params.id})
    ON CREATE SET 
        card.id = $params.id,
        card.name = $params.name
RETURN card
"""
create_node(kg, node_list_of_dicts=cards_list_of_dicts, query=merge_card_node_query)


merge_service_node_query = """
MERGE(service:SERVICE {id: $params.id})
    ON CREATE SET 
        service.id = $params.id,
        service.name = $params.name
RETURN service
"""
create_node(kg, node_list_of_dicts=services_list_of_dicts, query=merge_service_node_query)


merge_footnote_node_query = """
MERGE(footnote:FOOTNOTE {id: $params.id})
    ON CREATE SET 
        footnote.id = $params.id,
        footnote.note = $params.note
RETURN footnote
"""
create_node(kg, node_list_of_dicts=footnotes_list_of_dicts, query=merge_footnote_node_query)


merge_fee_rule_node_query = """
MERGE(fee_rule:FEE_RULE {id: $params.id})
    ON CREATE SET 
        fee_rule.id = $params.id,
        fee_rule.group_id = $params.group_id,
        fee_rule.description = $params.fee_rule,
        fee_rule.service = $params.service
RETURN fee_rule
"""
create_node(kg, node_list_of_dicts=fee_rules_list_of_dicts, query=merge_fee_rule_node_query)


###### 建立关系
# relationship_card_to_service_query = """
# MATCH
#   (card:CARD {id: $from_id}),
#   (service:SERVICE {id: $to_id})
# MERGE (card)-[r:HAS_SERVICE]->(service)
# RETURN count(r)
# """
# for card_id in cards_df["id"]:
#     for service_id in services_df["id"]:
#         kg.query(relationship_card_to_service_query, params={'from_id': card_id, 'to_id': service_id})
#         sleep(5)
#         print(f"Created relationship between card {card_id} and service {service_id}")


relationship_card_to_service_query = """
MATCH
  (card:CARD),
  (service:SERVICE)
MERGE (card)-[r:HAS_SERVICE]->(service)
RETURN count(r)
"""
kg.query(relationship_card_to_service_query)


relationship_service_to_fee_rule_query = """
MATCH
  (service:SERVICE),
  (fee_rule:FEE_RULE)
  WHERE fee_rule.group_id = service.id
MERGE (service)-[r:HAS_FEE_RULE]->(fee_rule)
RETURN count(r)
"""
kg.query(relationship_service_to_fee_rule_query)


relationship_fee_rule_to_footnote_query = """
MATCH
  (fee_rule:FEE_RULE {id: 1}),
  (footnote:FOOTNOTE {id: 1})
MERGE (fee_rule)-[r:HAS_FOOTNOTE]->(footnote)
RETURN count(r)
"""
kg.query(relationship_fee_rule_to_footnote_query)

print("stop")