import openai
import json
from typing import List
from pydantic import BaseModel, Field


def format_symptom_string(symptoms):
    res = ""
    for s in symptoms:
        res += f"{s['name']}: {s['description']}\n"
    return res


def format_system_message(symptoms, api_name):
    if api_name == "symptoms":
        symptom_string = format_symptom_string(symptoms)
        return f""" ## ROLE:You are an assistant to a therapist. 
## TASK: Your task is to read through passages from a patient's therapy journal.
Below, you are provided with a list of mental disorder symptoms and their descriptions. Please match the passage with
matching symptoms. 
## RESPONSE: Your response should contain:
    - list of symptoms if there are matches. If there is no match, return an empty list.
    - list of exerpts from the passage that makes you think there is a match between the passage and symptoms. If there is no match, return an empty list.
    - list of reasonings for why you think there is a match. If there is no match, return an empty list.
## SYMPTOMS AND THEIR DESCRIPTIONS:
{symptom_string}
"""
    elif api_name == "user_feedback":
        return """ ## ROLE:You are an assistant to a therapist. 
## TASK: Your task is to read through passages from a patient's therapy journal.
If there are especially insightful parts in the user passage, please provide feedback.
## EXAMPLE FEEDBACK:
    - Good job! You described your emotions very well here.
    - In this part, would you want to elaborate a bit on ...
    - When this happened, how did you feel? 
    - Don't be too harsh on yourself, you're doing really well!
"""


def format_user_message(passage):
    return f""" ## THERAPY JOURNAL PASSAGE:
    {passage}
    """

def get_openai_function_api(api_name):
    schema = None
    if api_name == "symptoms":
        class SymptomModel(BaseModel):
            "Output Schema for excerpts"

            symptom: str = Field(..., description="Name of the symptom expressed in the journal entry")
            excerpts: List[str] = Field(..., description="List of excerpts from the journal entry that you associate with a given symptom")
            reason: str = Field(..., description="Reason for why the symptom can be concluded from the excerpts")

        class QueryModel(BaseModel):
            "Output Schema for matching journal excerpts to symptoms."

            symptoms: List[SymptomModel]

        output_schema = QueryModel.schema()
        output_api = {
            "name": output_schema["title"],
            "description": output_schema["description"],
            "parameters": output_schema
        }
        schema = {
            'model': QueryModel,
            'api': output_api
        }

    elif api_name == "user_feedback":
        class QueryModel(BaseModel):
            "Output Schema for writing feedback for user passages"

            label: List[str] = Field(..., description="list of feedback labels for the user passages.")
            excerpt: List[str] = Field(..., description="list of exerpts from the passage that you are providing feedback on.")
            feedback: List[str] = Field(..., description="list of feedbacks you want to give the user.")

        output_schema = QueryModel.schema()
        output_api = {
            "name": output_schema["title"],
            "description": output_schema["description"],
            "parameters": output_schema
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
    result = json.loads(completion["function_call"]["arguments"])
    return schema['model'].parse_json(result)
