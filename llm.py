import os
import sys
import warnings
from typing import List

# Langchain
import dashscope
from langchain_community.llms import Tongyi
from dotenv import load_dotenv, find_dotenv
from langchain.embeddings.base import Embeddings


sys.path.append('../..')


_ = load_dotenv(find_dotenv()) 
load_dotenv('.env', override=True)
dashscope.api_key = os.environ['DASHSCOPE_API_KEY']
# Warning control
warnings.filterwarnings("ignore")

def get_qwen_llm():
    qwen_llm = Tongyi(
            model_name="qwen-plus",
            dashscope_api_key=dashscope.api_key
            )
    return qwen_llm


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