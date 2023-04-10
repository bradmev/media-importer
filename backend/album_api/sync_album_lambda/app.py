import sys
import logging
import os
import socket
import requests
import shutil
from requests_oauth2 import OAuth2BearerToken
import json
import boto3
import hashlib

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

s3 = boto3.client("s3")


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
        album_id = data["album_id"]
        email_hash = hashlib.md5(data["email"].encode()).hexdigest()

        # get album items list
        with requests.Session() as s:
            s.auth = OAuth2BearerToken(access_token)
            response = s.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                data={"pageSize": "100", "albumId": album_id},
            )
            response.raise_for_status()
            response_data = response.json()

        logger.debug(response_data)

        for item in response_data["mediaItems"]:
            # download the media to tmp
            logger.debug(f"Attempting to download {item['filename']}")
            tmp_filename = f"/tmp/{item['filename']}"
            r = requests.get(item["baseUrl"], stream=True)
            if r.status_code == 200:
                r.raw.decode_content = True
                with open(tmp_filename, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
                print("Image successfully Downloaded: ", tmp_filename)
            else:
                print("Image Couldn't be retrieved")

            # upload media to store bucket
            s3.upload_file(
                Filename=tmp_filename,
                Bucket="media-importer-store",
                Key=f"{email_hash}/{item['filename']}",
            )

        logger.debug("response data")
        logger.debug(json.dumps(response_data))

    except Exception as ex:
        logger.debug(ex)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps(ex),
        }
    finally:
        logger.debug("done")

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
        "body": json.dumps(response_data),
    }
