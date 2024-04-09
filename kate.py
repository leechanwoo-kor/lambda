import json

from constants import INTERACTION_CALLBACK_TYPE, REQUEST_TYPE
from utils import verify_request_signature, respond_pong, create_response


user_states = {}


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
        return create_response(400, "Bad Request")


def handle_command(body):
    command_name = body["data"]["name"]

    if command_name == "대화시작":
        return create_choice_response(body["member"]["user"]["username"])


def create_choice_response(user_id):
    message = f"안녕하세요, \@{user_id}님! 케이트와의 첫 만남이네요! 어떻게 하실 건가요?"
    components = [
        create_button("친절하게 인사하기", "greet", 1),
        create_button("무시하고 지나가기", "ignore", 4),
    ]
    return create_response_with_components(message, components)


def handle_interaction(interaction):
    user_id = interaction["member"]["user"]["username"]
    action_type = interaction["data"]["custom_id"]
    return handle_interaction_response(user_id, action_type)


def handle_interaction_response(user_id, action_type):
    # 사용자 상태 업데이트 로직을 한 곳에서 처리
    message, score_change = get_interaction_result(action_type)
    update_relationship_score(user_id, score_change)
    current_score = user_states.get(user_id, 0)
    relationship_info = f"\n\n현재 사용자 ID: {user_id} [호감도❤️ : {current_score}]"
    return create_response_with_components(
        message + relationship_info, get_next_interaction_components()
    )


def get_next_interaction_components():
    # 다음 상호작용을 위한 컴포넌트 리스트 반환
    return [
        create_button("이야기 나누기1", "learn_more", 1),
        create_button("이야기 나누기2", "share_story", 1),
    ]


def get_interaction_result(action_type):
    # action_type에 따른 메시지와 점수 변경을 관리
    outcomes = {
        "greet": ("와우, 정말 친절한 인사네요! 케이트, 기분이 좋아졌어요. 😀", 10),
        "ignore": ("오, 저를 무시하시는 건가요? 케이트가 조금 슬퍼졌어요. 😢", -5),
        # 추가 상호작용 결과
    }
    return outcomes.get(action_type, ("", 0))


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


def create_response_with_components(message, components):
    # 메시지와 컴포넌트를 포함한 응답 생성
    data = {
        "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "tts": False,
            "content": message,
            "components": [create_action_row(components)],
            "embeds": [],
        },
    }
    return create_response(200, data)


def create_action_row(components):
    return {"type": 1, "components": components}


def create_button(label, custom_id, style):
    return {"type": 2, "label": label, "style": style, "custom_id": custom_id}
