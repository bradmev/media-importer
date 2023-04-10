import sys
import logging
import os
import redis
import logging
import socket
import requests
import json
from requests_oauth2 import OAuth2BearerToken

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.info("## ENVIRONMENT VARIABLES")
    logger.info(os.environ)
    logger.info("## EVENT")
    logger.info(event)

    response_data = {}

    try:
        # decode payload
        data = json.loads(event["body"])
        access_token = data["access_token"]

        with requests.Session() as s:
            s.auth = OAuth2BearerToken(access_token)
            r = s.get("https://photoslibrary.googleapis.com/v1/albums")
            r.raise_for_status()
            data = r.json()

        logger.debug("response data")
        logger.debug(json.dumps(response_data))

    except Exception as ex:
        logger.debug(ex)
        return {"statusCode": 500}
    finally:
        # del redis_conn
        logger.debug("done")

    return {"statusCode": 200, "body": json.dumps(response_data)}
