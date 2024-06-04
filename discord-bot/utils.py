import json
from constants import INTERACTION_CALLBACK_TYPE


def respond_pong():
    return {
        "statusCode": 200,
        "body": json.dumps({"type": INTERACTION_CALLBACK_TYPE.PONG}),
        "headers": {"Content-Type": "application/json"},
    }


def create_response(status_code, data):
    return {
        "statusCode": status_code,
        "body": json.dumps(data),
        "headers": {"Content-Type": "application/json"},
    }


def create_response_with_image(message, image_url):
    response_body = {
        "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "tts": False,
            "content": message,
            "embeds": [],
        },
    }

    if image_url:
        embed = {"image": {"url": image_url}}
        response_body["data"]["embeds"].append(embed)

    return {
        "statusCode": 200,
        "body": json.dumps(response_body),
        "headers": {"Content-Type": "application/json"},
    }
