import os
import openai
import sys
# from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
sys.path.append('../..')

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['DASHSCOPE_API_KEY']


from langchain.document_loaders import PyPDFLoader
loader = PyPDFLoader("docs/Bank_Tariff_EN.pdf")
pages = loader.load()


## Token splitting

from langchain.text_splitter import TokenTextSplitter


text_splitter = TokenTextSplitter(chunk_size=30, chunk_overlap=10)

docs = text_splitter.split_documents(pages[3:4])

docs[0]

pages[0].metadata