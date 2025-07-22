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
VECTOR_INDEX_NAME = 'form_10k_chunks'
VECTOR_NODE_LABEL = 'Chunk'
VECTOR_SOURCE_PROPERTY = 'text'
VECTOR_EMBEDDING_PROPERTY = 'textEmbedding'


kg = Neo4jGraph(
    url=NEO4J_URI, 
    username=NEO4J_USERNAME, 
    password=NEO4J_PASSWORD, 
    database=NEO4J_DATABASE
)

# cypher_query = """
# CREATE 
#   (a1:A {name: 'A1', released: 1999}),
#   (b1:B {name: 'B1', released: 1999}),
#   (c1:C {name: 'C1', released: 1999}),
#   (matrix:Movie {name: 'The Matrix', released: 1999}),
#   (keanu:Person {name: 'Keanu Reeves', born: 1964}),
#   (laurence:Person {name: 'Laurence Fishburne', born: 1961}),
#   (keanu)-[:ACTED_IN {roles: ['Neo']}]->(matrix),
#   (laurence)-[:ACTED_IN {roles: ['Morpheus']}]->(matrix)
# """


cypher_query = """
CREATE 
  (a1:A {name: 'A1', released: 1999}),
  (b1:B {name: 'B1', released: 1999}),
  (c1:C {name: 'C1', released: 1999}),
  (b1)-[:ACTED_IN {roles: ['Neo']}]->(a1),
  (c1)-[:ACTED_IN {roles: ['Morpheus']}]->(a1)
"""


# Cypher MERGE 语句：为 title='The Matrix' 的电影节点增加 name='The Matrix' 属性
# kg.query("""
#     MERGE (m:Movie {title: 'The Matrix'})
#         ON CREATE SET m.name = 'The Matrix'
#     RETURN m
# """)


# 执行查询
kg.query(cypher_query)
print("✅ 已创建包含2人物1电影的知识图谱")

#### 删除s嗦哟nodes和relationshop
kg.query("""MATCH (n)
DETACH DELETE n""")


# 验证数据
result1 = kg.query("MATCH (n) RETURN n.name AS name, labels(n) AS type")
### 查看所有有关系的节点pairs
result2 = kg.query("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50")
### 查看所有的label
result3 = kg.query("CALL db.labels() YIELD label RETURN label")
### 查看特定节点的label
result4 = kg.query("""MATCH (n) 
                    RETURN n.name AS name, labels(n) AS type""")
### 查看特定标签的节点
result5 = kg.query("""MATCH (n:Movie) 
                        RETURN n""")
### 查看版本
result8 = kg.query("""RETURN "Neo4j " + version() AS version;""")
### 当前数据库的约束
result6 = kg.query("CALL db.constraints() YIELD name RETURN name")
### 当前数据库的索引
result7 = kg.query("CALL db.indexes() YIELD name RETURN name")



# print("\n图谱中的节点：")
# for row in result:
#     print(f"- {row['name']} ({'/'.join(row['type'])})")

# 关闭连接
# kg.close()
# kg.refresh_schema()
print(kg.schema)

print("stop")