import os
import openai
import sys
sys.path.append('../..')

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

# openai.api_key  = os.environ['DASHSCOPE_API_KEY']


from langchain.document_loaders import PyPDFLoader

# Load PDF
loaders = [
    # Duplicate documents on purpose - messy data
    PyPDFLoader("docs/Bank_Tariff_EN.pdf"),
    PyPDFLoader("docs/Bank_Tariff_EN.pdf")
]
docs = []
for loader in loaders:
    docs.extend(loader.load())


# Split
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1500,
    chunk_overlap = 150
)

splits = text_splitter.split_documents(docs)

len(splits)


######### OPENAI embeddings
# from langchain.embeddings.openai import OpenAIEmbeddings
# embedding = OpenAIEmbeddings()

# sentence1 = "i like dogs"
# sentence2 = "i like canines"
# sentence3 = "the weather is ugly outside"

# embedding1 = embedding.embed_query(sentence1)
# embedding2 = embedding.embed_query(sentence2)
# embedding3 = embedding.embed_query(sentence3)

# import numpy as np

# np.dot(embedding1, embedding2)

# np.dot(embedding1, embedding3)

# np.dot(embedding2, embedding3)


######### Qwen embeddings
import os
import dashscope
from dashscope import TextEmbedding
from typing import List
from langchain.embeddings.base import Embeddings
import numpy as np

# 设置 Qwen API Key（从环境变量读取）
dashscope.api_key = os.environ['DASHSCOPE_API_KEY']

# sentence1 = "i like dogs"
# sentence2 = "i like canines"
# sentence3 = "the weather is ugly outside"

# # 调用 Qwen 的 Embedding 模型
# response1 = TextEmbedding.call(
#     model="text-embedding-v1",  # Qwen 的 Embedding 模型
#     input=sentence1
# )
# response2 = TextEmbedding.call(
#     model="text-embedding-v1",  # Qwen 的 Embedding 模型
#     input=sentence2
# )
# response3 = TextEmbedding.call(
#     model="text-embedding-v1",  # Qwen 的 Embedding 模型
#     input=sentence3
# )
# embedding1 = response1.output['embeddings'][0]['embedding']
# embedding2 = response2.output['embeddings'][0]['embedding']
# embedding3 = response3.output['embeddings'][0]['embedding']


# np.dot(embedding1, embedding2)

# np.dot(embedding1, embedding3)

# np.dot(embedding2, embedding3)


###### 使用一个class
class QwenEmbeddings(Embeddings):
    def __init__(self, model_name="text-embedding-v1"):
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            response = dashscope.TextEmbedding.call(
                model=self.model_name,
                input=text
            )
            embeddings.append(response.output['embeddings'][0]['embedding'])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        response = dashscope.TextEmbedding.call(
            model=self.model_name,
            input=text
        )
        return response.output['embeddings'][0]['embedding']

# 使用方式
embedding = QwenEmbeddings()

sentence1 = "i like dogs"
sentence2 = "i like canines"
sentence3 = "the weather is ugly outside"

embedding1 = embedding.embed_query(sentence1)
embedding2 = embedding.embed_query(sentence2)
embedding3 = embedding.embed_query(sentence3)


np.dot(embedding1, embedding2)

np.dot(embedding1, embedding3)

np.dot(embedding2, embedding3)


######### Vector stores
from langchain.vectorstores import Chroma
persist_directory = 'docs/chroma/'
# !rm -rf ./docs/chroma  # remove old database files if any

vectordb = Chroma.from_documents(
    documents=splits[0:10],
    embedding=embedding,
    persist_directory=persist_directory
)

print(vectordb._collection.count())

###### similarity search
question = "这个文档是做什么的？"

docs = vectordb.similarity_search(question,k=3)

len(docs)

docs[0].page_content

#### Let's save this so we can use it later!
vectordb.persist()

