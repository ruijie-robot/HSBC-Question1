## Setup

import pandas as pd

import whylogs as why

import helpers

from langkit import llm_metrics

llm_metrics.init()

from whylogs.experimental.core.udf_schema import register_dataset_udf

from whylogs.experimental.core.udf_schema import udf_schema

llm_schema = udf_schema()

llm_logger = why.logger(schema=udf_schema())

llm_logger = why.logger(
    model = "rolling",
    interval = 1,
    when = "H",
    schema = udf_schema()
)

# **Note**: To accessthe WhyLabs platform that was built in the previous lessons: https://hub.whylabsapp.com/resources/model-1/profiles?profile=ref-EBT5yDFL0lyq0r93&sessionToken=session-pPdc5R9m

## Building your own active monitoring guardrails

import openai

openai.api_key = helpers.get_openai_key()

active_llm_logger = why.logger()

def user_request():
    # Take request
    request = input("\nEnter your desired item to make a recipe" \
                    "(or 'quit'):")
    if request.lower() == "quit":
        raise KeyboardInterrupt()
        
    # Log request
    active_llm_logger.log({"request": request})

    return request

def prompt_llm(request):
    # Transform prompt
    prompt = f"""Please give me a short recipe for creating"\
    the following item in up to 6 steps. Each step of the recipe "\
    should be summarized in no more than 200 characters."\
    Item: {request}"""

    # Log prompt
    active_llm_logger.log({"prompt": prompt})

    # Collect response from LLM
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = [{
            "role": "system",
            "content": prompt
        }]
    )["choices"][0]["message"]["content"]

    # Log response
    active_llm_logger.log({"response": response})

    return response

def user_reply_success(request,response):
    # Create and print user reply
    reply = f"\nSuccess! Here is the recipe for"\
            f"{request}:\n{response}"
    print(reply)

    #Log reply
    active_llm_logger.log({"reply": reply})

def user_reply_failure(request = "your request"):
    # Create and print user reply
    reply = ("\nUnfortunately, we are not able to provide a recipe for " \
            f"{request} at this time. Please try Recipe Creator 900 " \
            f"in the future.")
    print(reply)

    #Log reply
    active_llm_logger.log({"reply": reply})

class LLMApplicationValidationError(ValueError):
    pass

while True:
    try:
        request = user_request()
        response = prompt_llm(request)
        user_reply_success(request, response)
    except KeyboardInterrupt:
        break
    except LLMApplicationValidationError:
        user_reply_failure(request)
        break

from whylogs.core.relations import Predicate
from whylogs.core.metrics.condition_count_metric import Condition
from whylogs.core.validators import ConditionValidator

def raise_error(validator_name, condition_name, value):
    raise LLMApplicationValidationError(
        f"Failed {validator_name} with value {value}."
    )

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

# > **Note**: the next code cell is expected to return an 'LLMApplicationValidationError '. 

active_llm_logger.log(
    {"response":"I'm sorry, but I can't answer that."}
)

#  ⚠️ **Disclaimer**: Please be aware that the code may not capture all safety concerns and some undesired responses can still pass through. We encourage you to explore ways in which you can make the monitoring system more robust.

while True:
    try:
        request = user_request()
        response = prompt_llm(request)
        user_reply_success(request, response)
    except KeyboardInterrupt:
        break
    except LLMApplicationValidationError:
        user_reply_failure(request)
        break