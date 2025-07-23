from whylogs.experimental.core.udf_schema import register_dataset_udf
from whylogs.experimental.core.udf_schema import udf_schema
import pandas as pd
from langkit import sentiment
from transformers import pipeline
from span_marker import SpanMarkerModel


entity_model = SpanMarkerModel.from_pretrained(
    "tomaarsen/span-marker-bert-tiny-fewnerd-coarse-super"
)


def is_data_leakage(text):
    entities = entity_model.predict(text)
    flag = False
    for entity in entities:
        if entity["label"] == "PERSON":
            flag = True
    return flag