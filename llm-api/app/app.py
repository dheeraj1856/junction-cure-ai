import logging
import os
import json

import boto3
import openai

import utils
import llm

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger()


SYMPTOMS = json.loads('symptoms.json')
DISORDERS = json.loads('disorders.json')

def handler(event, context=None):
    request = get_request(event)
    