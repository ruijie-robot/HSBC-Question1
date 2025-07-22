import os
import sys
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv, find_dotenv
from langchain.document_loaders import PyPDFLoader
import os
import dashscope
from dashscope import TextEmbedding
from typing import List
from langchain.embeddings.base import Embeddings
import numpy as np
from langchain.vectorstores import Chroma


sys.path.append('../..')
_ = load_dotenv(find_dotenv())
persist_directory = 'docs/chroma/'
dashscope.api_key = os.environ['DASHSCOPE_API_KEY']


######### Qwen embeddings
###### 使用一个class把embedding包装起来
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


def test_embedding(embedding):
    sentence1 = "i like dogs"
    sentence2 = "i like cats"
    sentence3 = "the weather is ugly outside"

    embedding1 = embedding.embed_query(sentence1)
    embedding2 = embedding.embed_query(sentence2)
    embedding3 = embedding.embed_query(sentence3)


    np.dot(embedding1, embedding2)

    np.dot(embedding1, embedding3)

    np.dot(embedding2, embedding3)


def test_similarity_search(vectordb):
    question = "How much it is to request Photocopy of a cheque？"

    result = vectordb.similarity_search(question,k=3)

    len(result)

    result[0].page_content

def load_pdf_data():
    loader = PyPDFLoader("data/Bank_Tariff_EN.pdf")
    docs = loader.load()
    target_docs = [docs[3]] # 仅仅选取第4页作为测试
    return target_docs

def split_target_doc(target_docs):
    # Split
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 150
    )
    splits = text_splitter.split_documents(target_docs)
    len(splits)
    return splits


def main():
    target_docs = load_pdf_data()
    splits = split_target_doc(target_docs)
    embedding = QwenEmbeddings()

    vectordb = Chroma.from_documents(
    documents=splits,
    embedding=embedding,
    persist_directory=persist_directory
    )
    print(vectordb._collection.count())

    test_similarity_search(vectordb)
    vectordb.persist()

if __name__ == "__main__":
    main()