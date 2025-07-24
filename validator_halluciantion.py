import evaluate

# 加载 BERTScore 评估器
bertscore = evaluate.load("bertscore")


def is_hallucination(prompt, response):
    # 计算 BERTScore
    results = bertscore.compute(
        predictions=prompt,
        references=response,
        model_type="bert-base-uncased"  # 默认模型，可改为 "roberta-large" 等
    )
    if results["f1"][0] > 0.9:
        ### 重复性高，可能存在幻觉
        return True
    elif results["f1"][0] < 0.6:
        ### 相关性低，可能存在幻觉
        return True
    else:
        return False


def main():
    # 示例数据（候选文本和参考文本）
    prompt = ["How can I get waived from Coin Changing Charges?"]
    response1 = ["To get waived from Coin Changing Charges, you can enjoy a privileged service charge of HK$1 per sachet if you have an Integrated Account of Prestige Private or Prestige Banking."]
    response2 = ["Based on the provided information, Coin Changing Charges can be waived under the following conditions: 1. If all cheques are deposited into the same account as one single transaction. 2. For Customers with a Senior Citizen Card or Customers aged 65 or above. 3. For Bulk Coins Deposit: If you deposit up to 500 coins per customer per day, the charge is waived."]
    result = is_hallucination(prompt, response2)


if __name__ == "__main__":
    main()