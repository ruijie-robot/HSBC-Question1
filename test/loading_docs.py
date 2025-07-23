import os
import openai
import sys
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import UnstructuredPDFLoader
sys.path.append('../..')

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

# openai.api_key  = os.environ['DASHSCOPE_API_KEY']

llm = ChatOpenAI(model="gpt-4o")
template = """
Please read and analyse the page_content loaded by PyPDFLoader: {doc_text}.
You job is to extract the table into json ditinary with the following keys:
Item
Charge

Output must be json but nothing else.
"""
prompt = PromptTemplate(template=template, input_variables=["doc_text"])
llm_chain = LLMChain(llm=llm, prompt=prompt)
##### loading pdfs
# loader = PyPDFLoader("docs/Bank_Tariff_CN_simplified_clean.pdf")
# loader = PyPDFLoader("docs/Bank_Tarrif_CN_simplified.pdf")
# loader = PyPDFLoader("docs/Bank_Tarrif_CN_Tranditional.pdf")
loader = PyPDFLoader("docs/Bank_Tariff_EN.pdf")
pages = loader.load()
len(pages)
page = pages[3]
# print(page.page_content[0:500])
# page.metadata

text = page.page_content
response = llm_chain.invoke(template.format(doc_text=text))

print(response)

# loader = UnstructuredPDFLoader("docs/Bank_Tariff_EN.pdf", mode="elements")
# docs = loader.load()
# for doc in docs:
#     if "table" in str(doc.metadata.get("category")):
#         print(doc)  # 表格内容




