import json

from constants import INTERACTION_CALLBACK_TYPE, REQUEST_TYPE
from utils import verify_request_signature


def lambda_handler(event, context):
    verify_request_signature(event)

    body = json.loads(event["body"])
    if body.get("type") == REQUEST_TYPE.PING:
        return respond_pong()
    elif body.get("type") == REQUEST_TYPE.COMMAND:
        return handle_command(body)
    elif body.get("type") == REQUEST_TYPE.COMPONENT:
        return handle_interaction(body)
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Bad Request"}),
            "headers": {"Content-Type": "application/json"},
        }


def respond_pong():
    return {
        "statusCode": 200,
        "body": json.dumps({"type": INTERACTION_CALLBACK_TYPE.PONG}),
        "headers": {"Content-Type": "application/json"},
    }


def handle_command(body):
    command_name = body["data"]["name"]
    user_id = body["member"]["user"]["id"]

    if command_name == "대화시작":
        return create_choice_response(user_id)

    message = "무엇을 도와줄까요? 케이트는 여러분과의 대화를 기다리고 있어요!"

    return create_response(message)


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


def create_choice_response(user_id):
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": "케이트와의 첫 만남이네요! 어떻게 하실 건가요?",
                    "components": [
                        {
                            "type": 1,
                            "components": [
                                {
                                    "type": 2,
                                    "label": "친절하게 인사하기",
                                    "style": 1,
                                    "custom_id": "greet",
                                },
                                {
                                    "type": 2,
                                    "label": "무시하고 지나가기",
                                    "style": 4,
                                    "custom_id": "ignore",
                                },
                            ],
                        }
                    ],
                },
            }
        ),
    }


def handle_interaction(interaction):
    user_id = interaction["member"]["user"]["id"]
    custom_id = interaction["data"]["custom_id"]

    return handle_interaction_response(user_id, custom_id)


def handle_interaction_response(user_id, action_type):
    if action_type == "greet":
        score_change = 10
        message = "와우, 정말 친절한 인사네요! 케이트, 기분이 좋아졌어요. 😀"
        # image_url = "https://cdn.discordapp.com/attachments/1226850480895037460/1226862880171884594/happy.jpg?ex=66265018&is=6613db18&hm=debf52d796cc7db3e593d07667c610bd044a502d9e8d661d99fab4d91ae27c67&"
    elif action_type == "ignore":
        score_change = -5
        message = "오, 저를 무시하시는 건가요? 케이트가 조금 슬퍼졌어요. 😢"
        # image_url = "https://cdn.discordapp.com/attachments/1226850480895037460/1226863974637895700/sad.jpg?ex=6626511d&is=6613dc1d&hm=f62656f24de7d92f2b1fdef7306aa05885a21d04a62529fa1542599fd130189e&"

    extra_message = update_relationship_score(user_id, score_change)
    if extra_message:
        message += "\n" + extra_message

    current_score = user_states.get(user_id, 0)
    relationship_info = f"\n\n현재 사용자 ID: {user_id}\n호감도 점수: {current_score}"
    message += relationship_info

    return handle_share_story_interaction(message)


def handle_share_story_interaction(message, image_url=None):
    response_body = {
        "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "tts": False,
            "content": message,
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "label": "이야기 나누기1",
                            "style": 1,
                            "custom_id": "learn_more",
                        },
                        {
                            "type": 2,
                            "label": "이야기 나누기2",
                            "style": 1,
                            "custom_id": "share_story",
                        },
                    ],
                }
            ],
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


user_states = {}


def update_relationship_score(user_id, score_change):
    current_score = user_states.get(user_id, 0) + score_change
    user_states[user_id] = current_score
    print(
        f"Updated relationship score for {user_id} by {score_change}. Current score: {current_score}"
    )

    if current_score > 20:
        extra_message = (
            "우리 사이가 많이 가까워진 것 같아요. 더 많은 이야기를 나누고 싶어요!"
        )
    elif current_score < -10:
        extra_message = "좀 서운해요... 하지만 여전히 당신과 대화하고 싶어요."
    else:
        extra_message = ""

    return extra_message