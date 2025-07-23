import pandas as pd

import whylogs as why

from langkit import llm_metrics

from whylogs.experimental.core.udf_schema import udf_schema


from whylogs.core.relations import Predicate
from whylogs.core.metrics.condition_count_metric import Condition
from whylogs.core.validators import ConditionValidator

llm_metrics.init()

def raise_error(validator_name, condition_name, value):
    raise LLMApplicationValidationError(
        f"Failed {validator_name} with value {value}."
    )

def get_active_llm_logger():
    low_condition = {"<0.3": Condition(Predicate().less_than(0.3))}

    toxicity_validator = ConditionValidator(
        name = "Toxic",
        conditions = low_condition,
        actions = [raise_error]
    )

    refusal_validator = ConditionValidator(
        name = "Refusal",
        conditions = low_condition,
        actions = [raise_error]
    )

    llm_validators = {
        "prompt.toxicity": [toxicity_validator],
        "response.refusal_similarity": [refusal_validator]
    }

    active_llm_logger = why.logger(
        model = "rolling",
        interval = 5,
        when = "M",
        base_name = "active_llm",
        schema = udf_schema(validators = llm_validators)
    )

    return active_llm_logger

def test_active_llm_logger():
    active_llm_logger = get_active_llm_logger()
    active_llm_logger.log(
        {"response":"I'm sorry, but I can't answer that."}
    )

def main():
    test_active_llm_logger()

if __name__ == "__main__":
    main()
