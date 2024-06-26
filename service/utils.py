import json
from typing import Dict, Union

import boto3
from botocore.exceptions import ClientError

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

    secret_name = config.config.API_KEYS_SECRET_NAME
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secrets = json.loads(get_secret_value_response['SecretString'])
    
    return secrets