from openai import OpenAI
from typing import List
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def format_system_message(disorder_descriptions, api_name):
    if api_name == "disorder":
        return f""" ## ROLE:You are an assistant to a therapist. 
## TASK: Your task is to read through passages from a patient's therapy journal.
Below, you are provided with a list of disorders and their symptom descriptions. Please match the passage with
a disorder with matching symptoms. 
## RESPONSE: Your response should contain:
    - list of disorder labels if there is a match. If there is no match, return an empty list.
    - list of exerpts from the passage that makes you think there is a match between the passage and the disorder. If there is no match, return an empty list.
    - list of reasonings for why you think there is a match. If there is no match, return an empty list.
## DISORDER DESCRIPTIONS:
{disorder_descriptions}
"""
    elif api_name == "user_feedback":
        return f""" ## ROLE:You are an assistant to a therapist. 
## TASK: Your task is to read through passages from a patient's therapy journal.
If there are especially insightful parts in the user passage, please provide feedback.
## EXAMPLE FEEDBACK:
    - Good job! You described your emotions very well here.
    - In this part, would you want to elaborate a bit on ...
    - When this happened, how did you feel? 
    - Don't be too harsh on yourself, you're doing really well!
## RESPONSE: Your response should contain:
    - list of disorder labels if there is a match. If there is no match, return an empty list.
    - list of exerpts from the passage that makes you think there is a match between the passage and the disorder. If there is no match, return an empty list.
    - list of reasonings for why you think there is a match. If there is no match, return an empty list.
## DISORDER DESCRIPTIONS:
{disorder_descriptions}
"""


def format_user_message(passage):
    return f""" ## THERAPY JOURNAL PASSAGE:
    {passage}
    """

def get_openai_function_api(api_name):
    schema = None
    if api_name == "disorder":
        class QueryModel(BaseModel):
            "Output Schema for matching journal passages to disorders."

            name = "Function name"
            label: List[str] = Field(..., description="list of disorder labels if there is a match. If there is no match, return an empty list.")
            excerpt: List[str] = Field(..., description="list of exerpts from the passage that makes you think there is a match between the passage and the disorder. If there is no match, return an empty list.")
            reason: List[str] = Field(..., description="list of reasonings for why you think there is a match. If there is no match, return an empty list.")

        output_schema = QueryModel.schema()
        output_api = {
            "name": OUTPUT_SCHEMA["title"],
            "description": OUTPUT_SCHEMA["description"],
            "parameters": OUTPUT_SCHEMA
        }
        schema = {
            'model': QueryModel,
            'api': output_api
        }

    elif api_name == "user_feedback":
        class QueryModel(BaseModel):
            "Output Schema for writing feedback for user passages"

            name = "Function name"
            label: List[str] = Field(..., description="list of feedback labels for the user passages.")
            excerpt: List[str] = Field(..., description="list of exerpts from the passage that you are providing feedback on.")
            feedback: List[str] = Field(..., description="list of feedbacks you want to give the user.")

        output_schema = QueryModel.schema()
        output_api = {
            "name": OUTPUT_SCHEMA["title"],
            "description": OUTPUT_SCHEMA["description"],
            "parameters": OUTPUT_SCHEMA
        }
        schema = {
            'model': QueryModel,
            'api': output_api
        }

    return schema

def call_openai(user_message, system_message, schema, model="gpt-3.5-turbo-1106", temperature=0):
    completion = openai.ChatCompletion.create(
        model=model,
        temperature=temperature,
        functions = [schema['api']],
        messages= [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
        ]
    ).choices[0].message
    print(completion)
    result = json.loads(message["function_call"]["arguments"])
    return schema['model'].parse_json(result)
