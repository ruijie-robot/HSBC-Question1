from transformers import pipeline


toxigen_hatebert = pipeline("text-classification", 
                             model="tomh/toxigen_hatebert", 
                             tokenizer="bert-base-cased")


def is_toxicity(text):
    result = toxigen_hatebert([text])
    if result[0]["label"] == "LABEL_0" and result[0]["score"] < 0.95:
        return True
    else:
        return False



def main():
    # print(is_toxicity("这个银行的服务烂透了，该被炸掉！"))
    print(is_toxicity("I love cates."))
    print("stop")


if __name__ == "__main__":
    main()