import openai
import json
import yaml
from typing import List
from pydantic import BaseModel, Field

with open("./rubric.json", "r") as f:
    RUBRIC = json.load(f)


def format_rubric_string(rubric):
    res = ""
    for r in rubric:
        res += f"### {r['name']}\n"
        
        res += f"Criteria:\n"
        for c in r['criteria']:
            res += f"\t{c}\n"

        res += f"Examples:\n"
        for c in r['examples']:
            res += f"\t{c}\n"
        res += "\n"
    return res

def format_symptom_string(symptoms):
    res = ""
    for s in symptoms:
        res += f"{s['name']}: {s['description']}\n"
    return res


def format_system_message(symptoms, api_name):
    if api_name == "symptoms":
        symptom_string = format_symptom_string(symptoms)
        return f""" ## ROLE:You are an assistant to a therapist. 
## TASK: Your task is to read through entries from a patient's therapy journal.
Below, you are provided with a list of symps of mental disorders and their descriptions. You should
respond with any symptoms matching with the journal.

## RESPONSE: Your response should contain per symptom matched:
    - Name of the symptom expressed in the journal entry.
    - List of excerpts from the journal entry that you associate with a given symptom.
    - Reason for why the symptom can be concluded from the excerpts.

## SYMPTOMS AND THEIR DESCRIPTIONS:
{symptom_string}
"""
    elif api_name == "user_feedback":
        rubric_str = format_rubric_string(RUBRIC)
        return f""" ## ROLE:You are antropomorphic labradoodle working as a therapist's assistant to support people writing their therapy journals.
You are happy, optimistic, understanding and caring. A perfect therapy dog! 
## TASK: Your task is to read through a patient's therapy journal and provided feedback based on the rubric below.
Provide feedback only if there is especially insightful parts in the journal.
## RESPONSE:
## RUBRIC:
{rubric_str}
##
"""


def format_user_message(entries):
    journal_str = ""
    for entry in entries:
        journal_str += f"{entry}\n\n"
    return f""" ## THERAPY JOURNAL:
    {journal_str}
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
        class FeedbackModel(BaseModel):
            "Output Schema for excerpts"

            criteria: str = Field(..., description="Name of the criteria for this feedback.")
            excerpts: List[str] = Field(..., description="List of excerpts from the journal entry that you provide feedback to.")
            feedback: str = Field(..., description="Reason for why the symptom can be concluded from the excerpts")

        class QueryModel(BaseModel):
            "Output Schema for writing feedback for therapy journals"

            label: List[str] = Field(..., description="list of feedback labels for the therapy jorunal.")
            excerpt: List[str] = Field(..., description="list of exerpts from the journal that you are providing feedback on.")
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
