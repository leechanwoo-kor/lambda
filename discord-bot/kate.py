import requests
import json
from nacl.signing import VerifyKey
from constants import INTERACTION_CALLBACK_TYPE, REQUEST_TYPE
from utils import respond_pong, create_response

user_states = {}  # 사용자의 호감도를 관리하는 딕셔너리

DISCORD_PUBLIC_KEY = "<YOUR_PUBLIC_KEY>"

BASE_URL = "https://discord.com/api/v9"
TOKEN = "<YOUR_BOT_TOKEN>"


def delete_message(channel_id, message_id):
    headers = {
        "Authorization": f"Bot {TOKEN}",
    }
    url = f"{BASE_URL}/channels/{channel_id}/messages/{message_id}"
    response = requests.delete(url, headers=headers)
    return response


def lambda_handler(event, context):
    try:
        # 요청 검증
        auth_sig = event["headers"].get("x-signature-ed25519")
        auth_ts = event["headers"].get("x-signature-timestamp")
        raw_body = event["body"]
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{auth_ts}{raw_body}".encode(), bytes.fromhex(auth_sig))
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return create_response(401, "Unauthorized")

    body = json.loads(event["body"])
    return process_request(body)


def process_request(body):
    request_type = body.get("type")
    if request_type == REQUEST_TYPE.PING:
        return respond_pong()
    elif request_type in [REQUEST_TYPE.COMMAND, REQUEST_TYPE.COMPONENT]:
        return handle_request(body)
    else:
        return create_response(400, "Bad Request")


def handle_request(body):
    if body.get("type") == REQUEST_TYPE.COMMAND:
        return handle_command(body)
    elif body.get("type") == REQUEST_TYPE.COMPONENT:
        return handle_interaction(body)
    else:
        return create_response(400, "Unhandled Request Type")


def handle_command(body):
    command = body["data"]["name"]
    if command == "대화시작":
        return start_conversation()
    else:
        return create_response(400, "Invalid Command")


def handle_interaction(body):
    delete_message(body.get("channel_id"), body["message"]["id"])

    user_id = body["member"]["nick"]
    action_type = body["data"]["custom_id"]

    if action_type == "wait":
        return wait_for_kate(user_id)
    elif action_type == "help":
        return help_kate(user_id)
    elif action_type == "continue_talk":
        return continue_talk(user_id)
    elif action_type == "share_moment":
        return share_special_moment(user_id)
    elif action_type == "express_thanks":
        return auto(user_id)
    elif action_type == "auto":
        return end(body)
    else:
        return invalid_choice(user_id)


def auto(user_id):
    components = []

    message = "케이트가 죽었습니다. 어떻게 하시겠습니까?"
    components.append(create_button("어쩌지 내가 죽여버렸어", "auto", 1, -50))
    return update_and_create_response(user_id, message, components, -50)


def end(body):
    delete_message(body.get("channel_id"), body["message"]["id"])

    message = "케이트와의 대화가 종료되었습니다. 다음에 또 만나요!"

    response = {
        "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "tts": False,
            "content": message,
            "embeds": [],
        },
    }

    return create_response(200, response)


def start_conversation():
    message = "케이트가 바쁘게 움직이며 손님들을 응대하고 있어요. 그녀의 눈길이 잠깐 당신에게 닿습니다. '안녕하세요! 조금만 기다려 주실 수 있나요?' 그녀가 바쁘게 일하는 모습 속에서도 환하게 웃으며 인사를 건넵니다. 어떻게 할까요?"
    button_labels_and_custom_ids = [
        "인사하고 기다리기",
        "wait",
        "케이트의 일을 돕기",
        "help",
    ]

    components = [
        {"type": 2, "label": label, "style": 1, "custom_id": custom_id}
        for label, custom_id in zip(
            button_labels_and_custom_ids[::2], button_labels_and_custom_ids[1::2]
        )
    ]

    response = {
        "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "tts": False,
            "content": message,
            "components": [{"type": 1, "components": components}],
            "embeds": [],
        },
    }

    return create_response(200, response)


def update_and_create_response(user_id, message, components, score_change):
    update_relationship_score(user_id, score_change)
    current_score = user_states.get(user_id, 0)
    relationship_info = f"\n\n현재 사용자 ID: {user_id} [호감도❤️ : {current_score}]"
    return create_response_with_components(message + relationship_info, components)


def wait_for_kate(user_id):
    message = "케이트가 바쁜 모습을 이해하고, 조용히 기다립니다. 일이 끝난 후, 케이트가 당신에게 감사의 인사를 합니다."
    components = [create_button("이야기를 계속 나눈다", "continue_talk", 1, 5)]
    return update_and_create_response(user_id, message, components, 5)


def help_kate(user_id):
    message = "케이트의 일을 도와주며, 케이트는 당신의 친절에 감동받습니다. 일이 끝난 후, 둘은 함께 시간을 보냅니다."
    components = [create_button("이야기를 계속 나눈다", "continue_talk", 1, 10)]
    return update_and_create_response(user_id, message, components, 10)


def continue_talk(user_id):
    current_score = user_states.get(user_id, 0)
    components = []  # 버튼 컴포넌트를 담을 리스트 초기화

    if current_score < 15:
        message = "케이트는 한숨을 살짝 쉬며 이야기를 시작합니다. '오늘은 정말 바쁜 하루였어요. 그런데 당신이 오니까 마음이 좀 놓이네요.' 그녀의 표정이 한결 부드러워집니다."
        emotion = "😌"
        components.append(create_button("이야기를 계속 나눈다", "continue_talk", 1, 10))
    elif current_score < 25:
        message = "케이트는 당신과 대화하며 활짝 웃습니다. '사실, 요즘 새로운 취미를 찾았어요. 사진 찍기예요! 나중에 한 번 보여드릴게요.' 그녀의 눈빛이 반짝입니다."
        emotion = "😊"
        # 기본 대화 계속하기 버튼 추가
        components.append(create_button("이야기를 계속 나눈다", "continue_talk", 1, 10))
    else:
        message = "케이트는 당신과의 대화가 너무 좋아 보입니다. '이렇게 좋은 사람과 시간을 보낼 수 있어서 행복해요. 우리 더 자주 만나요!' 그녀는 진심으로 그렇게 말합니다."
        emotion = "😍"
        # 대화를 더 깊게 나눌 수 있는 새로운 버튼 추가
        components.append(
            create_button("특별한 순간을 공유하다", "share_moment", 2, 10)
        )
        components.append(create_button("이야기를 계속 나눈다", "continue_talk", 1, 10))

    message += f" {emotion}"

    return update_and_create_response(user_id, message, components, 10)


def share_special_moment(user_id):
    components = []

    message = (
        "케이트와 당신은 공원을 산책하며 서로에 대한 이야기를 나눕니다. "
        "케이트는 당신과의 대화를 통해 자신의 꿈과 희망에 대해 더 깊이 있게 공유합니다. "
        "'이런 특별한 순간을 당신과 함께 할 수 있어서 정말 행복해요.'라고 케이트가 말하며, "
        "당신의 손을 잡습니다. 당신의 관계는 이제 막 특별한 단계로 나아가고 있음을 느낍니다."
    )

    components = [create_button("감사의 마음을 전하다", "express_thanks", 1, 10)]

    return update_and_create_response(user_id, message, components, 10)


def invalid_choice(user_id):
    components = []

    message = "케이트가 죽었습니다. 어떻게 하시겠습니까?"
    components.append(create_button("어떡해", "auto", 1, 0))
    components.append(create_button("어떡해", "auto", 1, 0))
    return update_and_create_response(user_id, message, components, 0)


def create_response_with_components(message, components):
    action_row = {"type": 1, "components": components}

    data = {
        "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "tts": False,
            "content": message,
            "components": [action_row],
            "embeds": [],
        },
    }
    return create_response(200, data)


def create_button(label, custom_id, style, score_change=0):
    return {
        "type": 2,
        "label": label,
        "style": style,
        "custom_id": custom_id,
        "score_change": score_change,
    }


def update_relationship_score(user_id, score_change):
    # 기존 호감도 업데이트 로직
    previous_score = user_states.get(user_id, 0)
    new_score = previous_score + score_change
    user_states[user_id] = new_score
