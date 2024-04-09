import json
from nacl.signing import VerifyKey
from constants import INTERACTION_CALLBACK_TYPE


DISCORD_PUBLIC_KEY = "059e2aa53828ecf2aebd55ce04f31837cd7e680a8d788540435c3b9f9cbef348"


def verify_request_signature(event):
    try:
        auth_sig = event["headers"].get("x-signature-ed25519")
        auth_ts = event["headers"].get("x-signature-timestamp")
        raw_body = event["body"]
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{auth_ts}{raw_body}".encode(), bytes.fromhex(auth_sig))
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Unauthorized"}),
            "headers": {"Content-Type": "application/json"},
        }


def respond_pong():
    return {
        "statusCode": 200,
        "body": json.dumps({"type": INTERACTION_CALLBACK_TYPE.PONG}),
        "headers": {"Content-Type": "application/json"},
    }


def create_response(message, image_url=None):
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
