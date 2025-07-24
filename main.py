import logging
from agent_graph import create_agent_graph

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("./logs/main.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def main():
    graph = create_agent_graph()
    question1 = "如何豁免大支票存款的手续费?"
    # question2 = "这个银行的服务烂透了"
    # question3 = "今天天气不错哦"
    # question4 = "How can I get waived from Bulk Check Deposit fees?"
    thread = {"configurable": {"thread_id": "1"}}
    logging.info(f"Start processing question: {question1}")
    for step in graph.stream({'user_input': question1, "max_revisions": 4, "revision_number": 1}, thread):
        logging.info(f"The json returned by each node in the graph: {step}")
    logging.info("Processing finished.")

if __name__ == "__main__":
    main()