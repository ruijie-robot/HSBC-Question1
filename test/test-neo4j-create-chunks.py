from dotenv import load_dotenv
import os

# Common data processing
import json
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
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Note the code below is unique to this course environment, and not a 
# standard part of Neo4j's integration with OpenAI. Remove if running 
# in your own environment.
OPENAI_ENDPOINT = os.getenv('OPENAI_BASE_URL') + '/embeddings'

# Global constants
VECTOR_INDEX_NAME = 'form_10k_chunks'
VECTOR_NODE_LABEL = 'Chunk'
VECTOR_SOURCE_PROPERTY = 'text'
VECTOR_EMBEDDING_PROPERTY = 'textEmbedding'


first_file_name = "./data/form10k/0000950170-23-027948.json"

first_file_as_object = json.load(open(first_file_name))

type(first_file_as_object)

for k,v in first_file_as_object.items():
    print(k, type(v))

item1_text = first_file_as_object['item1']

item1_text[0:1500]

##### Split Form 10-K sections into chunks
######## split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 2000,
    chunk_overlap  = 200,
    length_function = len,
    is_separator_regex = False,
)

item1_text_chunks = text_splitter.split_text(item1_text)

type(item1_text_chunks)

len(item1_text_chunks)

item1_text_chunks[0]


def split_form10k_data_from_file(file):
    chunks_with_metadata = [] # use this to accumlate chunk records
    file_as_object = json.load(open(file)) # open the json file
    for item in ['item1','item1a','item7','item7a']: # pull these keys from the json
        print(f'Processing {item} from {file}') 
        item_text = file_as_object[item] # grab the text of the item
        item_text_chunks = text_splitter.split_text(item_text) # split the text into chunks
        chunk_seq_id = 0
        for chunk in item_text_chunks[:20]: # only take the first 20 chunks
            form_id = file[file.rindex('/') + 1:file.rindex('.')] # extract form id from file name
            # finally, construct a record with metadata and the chunk text
            chunks_with_metadata.append({
                'text': chunk, 
                # metadata from looping...
                'f10kItem': item,
                'chunkSeqId': chunk_seq_id,
                # constructed metadata...
                'formId': f'{form_id}', # pulled from the filename
                'chunkId': f'{form_id}-{item}-chunk{chunk_seq_id:04d}',
                # metadata from file...
                'names': file_as_object['names'],
                'cik': file_as_object['cik'],
                'cusip6': file_as_object['cusip6'],
                'source': file_as_object['source'],
            })
            chunk_seq_id += 1
        print(f'\tSplit into {chunk_seq_id} chunks')
    return chunks_with_metadata


first_file_chunks = split_form10k_data_from_file(first_file_name)

first_file_chunks[0]


### Create graph nodes using text chunks
### merge语法：如果节点存在，匹配现有节点，否则创建新的
merge_chunk_node_query = """
MERGE(mergedChunk:Chunk {chunkId: $chunkParam.chunkId})
    ON CREATE SET 
        mergedChunk.names = $chunkParam.names,
        mergedChunk.formId = $chunkParam.formId, 
        mergedChunk.cik = $chunkParam.cik, 
        mergedChunk.cusip6 = $chunkParam.cusip6, 
        mergedChunk.source = $chunkParam.source, 
        mergedChunk.f10kItem = $chunkParam.f10kItem, 
        mergedChunk.chunkSeqId = $chunkParam.chunkSeqId, 
        mergedChunk.text = $chunkParam.text
RETURN mergedChunk
"""

kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)

kg.query(merge_chunk_node_query, 
         params={'chunkParam':first_file_chunks[0]})


kg.query("""
CREATE CONSTRAINT unique_chunk IF NOT EXISTS 
    FOR (c:Chunk) REQUIRE c.chunkId IS UNIQUE
""")


kg.query("SHOW INDEXES")

### Loop through and create nodes for all chunks
node_count = 0
for chunk in first_file_chunks:
    print(f"Creating `:Chunk` node for chunk ID {chunk['chunkId']}")
    kg.query(merge_chunk_node_query, 
            params={
                'chunkParam': chunk
            })
    node_count += 1
print(f"Created {node_count} nodes")

kg.query("""
         MATCH (n)
         RETURN count(n) as nodeCount
         """)


### Create a vector index
kg.query("""
         CREATE VECTOR INDEX `form_10k_chunks` IF NOT EXISTS
          FOR (c:Chunk) ON (c.textEmbedding) 
          OPTIONS { indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'    
         }}
""")

kg.query("SHOW INDEXES")

### Calculate embedding vectors for chunks and populate index
kg.query("""
    MATCH (chunk:Chunk) WHERE chunk.textEmbedding IS NULL
    WITH chunk, genai.vector.encode(
      chunk.text, 
      "OpenAI", 
      {
        token: $openAiApiKey, 
        endpoint: $openAiEndpoint
      }) AS vector
    CALL db.create.setNodeVectorProperty(chunk, "textEmbedding", vector)
    """, 
    params={"openAiApiKey":OPENAI_API_KEY, "openAiEndpoint": OPENAI_ENDPOINT} )

kg.refresh_schema()
print(kg.schema)

### Use similarity search to find relevant chunks
def neo4j_vector_search(question):
  """Search for similar nodes using the Neo4j vector index"""
  vector_search_query = """
    WITH genai.vector.encode(
      $question, 
      "OpenAI", 
      {
        token: $openAiApiKey,
        endpoint: $openAiEndpoint
      }) AS question_embedding
    CALL db.index.vector.queryNodes($index_name, $top_k, question_embedding) yield node, score
    RETURN score, node.text AS text
  """
  similar = kg.query(vector_search_query, 
                     params={
                      'question': question, 
                      'openAiApiKey':OPENAI_API_KEY,
                      'openAiEndpoint': OPENAI_ENDPOINT,
                      'index_name':VECTOR_INDEX_NAME, 
                      'top_k': 10})
  return similar


search_results = neo4j_vector_search(
    'In a single sentence, tell me about Netapp.'
)

search_results[0]


### Set up a LangChain RAG workflow to chat with the form
neo4j_vector_store = Neo4jVector.from_existing_graph(
    embedding=OpenAIEmbeddings(),
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    index_name=VECTOR_INDEX_NAME,
    node_label=VECTOR_NODE_LABEL,
    text_node_properties=[VECTOR_SOURCE_PROPERTY],
    embedding_node_property=VECTOR_EMBEDDING_PROPERTY,
)

retriever = neo4j_vector_store.as_retriever()

chain = RetrievalQAWithSourcesChain.from_chain_type(
    ChatOpenAI(temperature=0), 
    chain_type="stuff", 
    retriever=retriever
)

def prettychain(question: str) -> str:
    """Pretty print the chain's response to a question"""
    response = chain({"question": question},
        return_only_outputs=True,)
    print(textwrap.fill(response['answer'], 60))

question = "What is Netapp's primary business?"

prettychain(question)

prettychain("Where is Netapp headquartered?")

prettychain("""
    Tell me about Netapp. 
    Limit your answer to a single sentence.
""")

prettychain("""
    Tell me about Apple. 
    Limit your answer to a single sentence.
""")




