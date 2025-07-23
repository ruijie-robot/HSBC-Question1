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

### 查看所有有关系的节点pairs
# result = kg.query("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50")
# result = kg.query("MATCH (c:CARD {id: 0}) RETURN count(c)", params={})
# result = kg.query("""MATCH (s:SERVICE)-[r:HAS_FEE_RULE]->(f:FEE_RULE)
#                     RETURN count(r) AS actual_count""")

# result = kg.query("""MATCH (s:SERVICE)-[r:HAS_FEE_RULE]->(f:FEE_RULE)
# RETURN 
#   s.id AS service_id,
#   s.name AS service_name,
#   f.id AS fee_rule_id,
#   f.group_id AS fee_rule_group,
#   f.description AS fee_rule_description,
#   type(r) AS relationship_type
# ORDER BY service_id, fee_rule_id""")

# result = kg.query("""MATCH (service:SERVICE)-[:HAS_FEE_RULE]->(fee_rule:FEE_RULE)
#     WHERE service.name = 'Bulk Cheque Deposit'
# RETURN fee_rule.description""")

# result = kg.query("""MATCH (service:SERVICE)-[:HAS_FEE_RULE]->(fee_rule:FEE_RULE)
#     OPTIONAL MATCH (service:SERVICE)-[:HAS_FEE_RULE]->(fee_rule:FEE_RULE)-[:HAS_FOOTNOTE]->(footnote:FOOTNOTE)
#     WHERE service.name = 'Bulk Cheque Deposit'
#     RETURN service.name, fee_rule.description, footnote.text""")

#### 会返回和service连接的所有node
result = kg.query("""MATCH (fee_rule:FEE_RULE)-[r:HAS_FOOTNOTE]->(footnote:FOOTNOTE)
RETURN fee_rule.id, footnote.id""")


# result = kg.query("""MATCH (service:SERVICE)-[r:HAS_FEE_RULE]->(fee_rule:FEE_RULE)
#     RETURN service.id, fee_rule.id""")

print(result)

print("stop")