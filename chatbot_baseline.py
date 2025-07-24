import sys

from llm import get_qwen_llm
from langchain.chains import RetrievalQA
from vectordb import get_vectordb
### Prompt
from langchain.prompts import PromptTemplate
from questions import get_question_library

sys.path.append('../..')

def test_similarity_search(vectordb):
    question = "What are major topics for this class?"
    docs = vectordb.similarity_search(question,k=3)
    len(docs)

def test_on_refine_chain():
    qwen_llm = get_qwen_llm()
    vectordb = get_vectordb()

    questions = get_question_library()

    # Build prompt
    GENERATION_TEMPLATE = """Use the following pieces of context to answer the question at the end. If you don't know the answer, 
    just say that you don't know, don't try to make up an answer. Use three sentences maximum. Keep the answer as concise as possible. 
    {context_str}
    Question: {question}
    Helpful Answer:"""
    QA_CHAIN_PROMPT = PromptTemplate.from_template(GENERATION_TEMPLATE)

    REFINE_TEMPLATE = """The original question is as follows: {question}
    We have provided an existing answer: {existing_answer}
    We have the opportunity to refine the existing answer with some more context below.
    {context_str}
    Given the new context, refine the original answer. If the context isn't useful, return the original answer."""

    # QA_CHAIN_REFINE_PROMPT = PromptTemplate.from_template(REFINE_TEMPLATE)
    QA_CHAIN_REFINE_PROMPT = PromptTemplate(
    input_variables=["question", "existing_answer", "context"],
    template=REFINE_TEMPLATE
    )

    # Use refine chain
    qa_chain = RetrievalQA.from_chain_type(
        qwen_llm,
        retriever=vectordb.as_retriever(k=3),
        chain_type="refine",
        return_source_documents=True,
        chain_type_kwargs={"question_prompt": QA_CHAIN_PROMPT, 
                            "refine_prompt": QA_CHAIN_REFINE_PROMPT}
    )

    result = qa_chain({"query": questions[4]})
    result["result"]
    result["source_documents"][0]

### 把qa_chain建立起来，方便调用
def call_chain():
    qwen_llm = get_qwen_llm()
    vectordb = get_vectordb()

    qa_chain = RetrievalQA.from_chain_type(
        qwen_llm,
        retriever=vectordb.as_retriever(k=3),
        chain_type="map_reduce",
        return_source_documents=True
    )
    return qa_chain

def get_response(qa_chain, question):
    try:
        result = qa_chain({"query": question})
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I donnot know."
    # print(result["result"])
    return result["result"]

def main():
    # qwen_llm = get_qwen_llm()
    # vectordb = get_vectordb()
    qa_chain = call_chain()

    questions = get_question_library(type="test")
    # question = "How can I get waived from Bulk Cheque Deposit fees?"
    # question = "How much does the Bulk Cheque Deposit cost?"
    # question = "What is the difference between Integrated Account Card of Prestige Private and Integrated Account Card of Prestige Banking"
    question = "How can I get waived from Coin Changing Charges?"
    response = get_response(qa_chain, question)
    print(f"question: {question}\nresponse: {response}")

    print("Done")
    # result["source_documents"][0]

if __name__ == "__main__":
    main()

