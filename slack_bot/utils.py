import json
import os
from typing import Dict, Union

import requests

import config

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def build_response(body: Union[Dict, str]):
    """Builds response for Lambda"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def get_secrets() -> Dict[str, str]:
    """Fetches the API keys saved in Secrets Manager"""

    headers = {
        "X-Aws-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN')
    }
    secrets_extension_endpoint = "http://localhost:2773" + \
    "/secretsmanager/get?secretId=" + \
    config.config.API_KEYS_SECRET_NAME
    
    logging.info(secrets_extension_endpoint)

    r = requests.get(secrets_extension_endpoint, headers=headers)

    logging.info(r.text)

    secrets = json.loads(json.loads(r.text)["SecretString"])

    return secrets