from langchain_community.llms import Tongyi
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv,find_dotenv
import json

# 加载环境变量
_ = load_dotenv(find_dotenv()) # read local .env file

# 初始化 Qwen 模型
llm = Tongyi(
    model_name="qwen-plus",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
)

# 定义提示模板
template = """请根据下面的文档内容，回答Request for Banker’s report需要多少钱?：
{text}
"""
prompt = PromptTemplate(template=template, input_variables=["text"])
chain = LLMChain(llm=llm, prompt=prompt)

# 调用模型
text = "A. Deposit Account and Services\nItem Charge\nBulk Cheque Deposit – Per customer per day\n- Up to 30 pieces\n- Over 30 pieces\nWaived\nHK$1 per additional cheque (1)\nBulk Cash Deposit – Per customer per day\n- HKD / RMB Notes:\n - Up to 200 pieces of notes\n - Over 200 pieces of notes\n- Foreign Currency notes\nWaived\n0.25% on deposit amount (min. HK$50)\nWaived\nBulk Coins Deposit – Per customer per day\n- Up to 500 coins\n- Over 500 coins\nWaived\n2% on deposit amount (min. HK$50)\nCoin Changing Charges HK$2 per sachet (2)\nReplacement of Card\nHang Seng Card (3)(4)/Integrated Account Card of Prestige Private/\nIntegrated Account Card of Prestige Banking/Integrated Account \nCard of Preferred Banking/Integrated Account Card\nHK$50 per card\nPaper Statement (3)(4)(5) HK$60 per account (For every 12 months period from July to June \nof the following year)\nRequest for Banker’s report/document copies (6)\n- Account History Record of Savings or Time Deposit Accounts\n - For 1 Year\n - For 2 Years\n - For 3 Years\n - For more than 3 years\n- Photocopy of\n - statement (per cycle)\n - cheque (per copy)\n - voucher (per copy)\n - transaction advice (per copy)\n- Issuance of Overdraft Interest Statement\n- Banker’s Endorsement on Customer’s Signature\n- Personal data access request (7)\n- Reference Letter\n- Certificate of Account Balance\n- Certificate of Deposit Interest Earned\nHK$250 per account\nHK$750 per account\nHK$1,000 per account\nHK$1,000 per year thereafter\nHK$50 per cycle or per copy\n(No service charge for applying a copy of the consolidation statement\nlisting the unposted items of passbook account.)\nHK$300 per copy per cycle\nHK$150 per item\nCircumstantial (maximum HK$500 per request)\nWaived\nWaived\nWaived\nNotes\n(1) Waived if all cheques are deposited into the same account as one single transaction.\n(2) Integrated Account of Prestige Private/Prestige Banking can enjoy a privileged service charge of HK$1 per sachet.\n(3) Waived for Customers with Senior Citizen Card or Customers aged 65 or above.\n(4) Exemptions apply to customers aged below 18, recipients of Comprehensive Social Security Assistance (supporting documents required) and persons who present a \nproof of disability document (e.g. document of receiving government disability allowance).\n(5) Applicable to personal accounts including Prestige Private, Prestige Banking, Preferred Banking, Integrated Account, Family+ Account, HKD Current Account, HKD \nStatement Savings Account and ATM Statement Savings Account. A fee of HK$60 per account will be charged if customers receive more than 2 paper statements for \nevery 12 months from July to June of the following year. \n(6) Upon customer request for delivery by local and overseas courier services, courier handling fee will be charged on actual.\n(7) This standard concessionary charge applies to the first time and normal data access request. In other cases, the Bank reserves the right to charge the actual commercial \ncost incurred without applying a cap to the charge. However, in any case, the Bank will inform the data requestor individually the actual handling charge and will only \nprocess the request upon receiving the requestor’s acceptance.\nThis page has been revised since 1 October 2024.- 1 -\nPPL489-R88 (07/2025) (HH)'"
response = chain.invoke({"text": text})
response = response["text"]
response = response.replace("```json", "").replace("```", "")
data = json.loads(response)
print(response["text"])