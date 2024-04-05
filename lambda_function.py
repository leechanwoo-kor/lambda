import json
from dataclasses import dataclass

from nacl.signing import VerifyKey


@dataclass
class INTERACTION_CALLBACK_TYPE:
    # https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-response-object
    PONG = 1
    ACK_NO_SOURCE = 2
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9
    PREMIUM_REQUIRED = 10


@dataclass
class REQUEST_TYPE:
    PING = 1
    BUTTON = 3
    MODAL = 5


# 디스코드 개발자 포털에 General Information page에서 확인할 수 있습니다.
DISCORD_PUBLIC_KEY = '<your public key here>'


def lambda_handler(event, context):
    print(json.dumps(event))  # 디버깅용

    # signature 검증
    try:
        raw_body = event['body']
        auth_sig = event['headers'].get('x-signature-ed25519')
        auth_ts = event['headers'].get('x-signature-timestamp')

        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(
            f'{auth_ts}{raw_body}'.encode(),
            bytes.fromhex(auth_sig)
        )
    except Exception as e:
        raise Exception(f"[UNAUTHORIZED] Invalid request signature: {e}")

    body = json.loads(raw_body)

    # ping pong
    if body.get("type") == REQUEST_TYPE.PING:
        return {
            'statusCode': 200,
            'body': json.dumps(
                {
                    'type': 1
                }
            )
        }

    # 응답
    return {
        'statusCode': 200,
        'body': json.dumps(
            {
                "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "tts": False,
                    "content": "테스트 응답입니다.",
                    "embeds": []
                }
            }
        )
    }