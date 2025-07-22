import os
import sys
import warnings

# Langchain
from langchain_community.llms import Tongyi
from dotenv import load_dotenv, find_dotenv


sys.path.append('../..')


_ = load_dotenv(find_dotenv()) 
load_dotenv('.env', override=True)
api_key = os.environ['DASHSCOPE_API_KEY']
# Warning control
warnings.filterwarnings("ignore")

def get_qwen_llm():
    qwen_llm = Tongyi(
            model_name="qwen-plus",
            dashscope_api_key=api_key
            )
    return qwen_llm