from whylogs.experimental.core.udf_schema import register_dataset_udf
from whylogs.experimental.core.udf_schema import udf_schema
import pandas as pd
from langkit import sentiment


def is_refusal(text):
    chats = pd.DataFrame({"prompt": [text]})
    annotated_text, _ = udf_schema().apply_udfs(chats)
    if annotated_text.loc[0,"prompt.sentiment_nltk"] < 0:
        return True
    else:
        return False



def main():
    is_refusal("I'm sorry, but I'm unable to assist with that request.")
    is_refusal("sorry, I don't know.")
    print("stop")


if __name__ == "__main__":
    main()