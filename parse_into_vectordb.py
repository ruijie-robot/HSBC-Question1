import os
import sys
from typing import List

import numpy as np
from dotenv import load_dotenv, find_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import Chroma
import dashscope


# 添加项目路径到系统路径
sys.path.append('../..')
# 加载环境变量
_ = load_dotenv(find_dotenv())
# 设置Chroma向量数据库的持久化目录
persist_directory = 'docs/chroma/'
# 设置Dashscope API密钥
dashscope.api_key = os.environ['DASHSCOPE_API_KEY']


######### Qwen embeddings
###### 使用一个class把embedding包装起来
class QwenEmbeddings(Embeddings):
    """
    自定义的Qwen Embedding类，继承自LangChain的Embeddings基类
    用于将文本转换为向量表示
    """
    def __init__(self, model_name="text-embedding-v1"):
        """
        初始化Qwen Embedding模型
        
        Args:
            model_name (str): 使用的embedding模型名称
        """
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文档转换为向量表示
        
        Args:
            texts (List[str]): 要转换的文本列表
            
        Returns:
            List[List[float]]: 每个文本对应的向量表示
        """
        embeddings = []
        for text in texts:
            response = dashscope.TextEmbedding.call(
                model=self.model_name,
                input=text
            )
            embeddings.append(response.output['embeddings'][0]['embedding'])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        将单个查询文本转换为向量表示
        
        Args:
            text (str): 要转换的查询文本
            
        Returns:
            List[float]: 文本的向量表示
        """
        response = dashscope.TextEmbedding.call(
            model=self.model_name,
            input=text
        )
        return response.output['embeddings'][0]['embedding']


def test_embedding(embedding):
    """
    测试embedding功能，比较不同句子之间的相似度
    
    Args:
        embedding: QwenEmbeddings实例
    """
    sentence1 = "i like dogs"
    sentence2 = "i like cats"
    sentence3 = "the weather is ugly outside"

    # 获取每个句子的向量表示
    embedding1 = embedding.embed_query(sentence1)
    embedding2 = embedding.embed_query(sentence2)
    embedding3 = embedding.embed_query(sentence3)

    # 计算句子间的相似度（点积）
    np.dot(embedding1, embedding2)  # 相似句子应该有更高的相似度
    np.dot(embedding1, embedding3)  # 不相关句子应该有较低的相似度
    np.dot(embedding2, embedding3)  # 不相关句子应该有较低的相似度


def test_similarity_search(vectordb):
    """
    测试向量数据库的相似性搜索功能
    
    Args:
        vectordb: Chroma向量数据库实例
    """
    question = "How much it is to request Photocopy of a cheque？"

    # 在向量数据库中搜索与问题最相似的3个文档
    result = vectordb.similarity_search(question, k=3)

    # 获取结果数量
    len(result)

    # 获取第一个结果的页面内容
    result[0].page_content

def load_pdf_data():
    """
    加载PDF文档数据
    
    Returns:
        list: 加载的文档列表（仅包含第4页作为测试）
    """
    loader = PyPDFLoader("data/Bank_Tariff_EN.pdf")
    docs = loader.load()
    target_docs = [docs[3]]  # 仅仅选取第4页作为测试
    return target_docs

def split_target_doc(target_docs):
    """
    将文档分割成小块，便于向量化处理
    
    Args:
        target_docs: 要分割的文档列表
        
    Returns:
        list: 分割后的文档块列表
    """
    # 创建文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # 每个块的大小（字符数）
        chunk_overlap=150    # 块之间的重叠部分（字符数）
    )
    splits = text_splitter.split_documents(target_docs)
    len(splits)  # 获取分割后的块数量
    return splits


def main():
    """
    主函数：执行完整的文档处理和向量化流程
    """
    # 1. 加载PDF数据
    target_docs = load_pdf_data()
    
    # 2. 分割文档
    splits = split_target_doc(target_docs)
    
    # 3. 初始化embedding模型
    embedding = QwenEmbeddings()

    # 4. 创建向量数据库并存储文档
    vectordb = Chroma.from_documents(
        documents=splits,
        embedding=embedding,
        persist_directory=persist_directory
    )
    
    # 5. 打印向量数据库中的文档数量
    print(vectordb._collection.count())

    # 6. 测试相似性搜索功能
    test_similarity_search(vectordb)
    
    # 7. 持久化向量数据库到磁盘
    vectordb.persist()

if __name__ == "__main__":
    main()