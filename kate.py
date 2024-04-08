import json
from nacl.signing import VerifyKey

from dataclasses import dataclass


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
    COMMAND = 2
    COMPONENT = 3
    MODAL = 5


DISCORD_PUBLIC_KEY = '059e2aa53828ecf2aebd55ce04f31837cd7e680a8d788540435c3b9f9cbef348'

def verify_request_signature(event):
    try:
        auth_sig = event['headers'].get('x-signature-ed25519')
        auth_ts = event['headers'].get('x-signature-timestamp')
        raw_body = event['body']
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f'{auth_ts}{raw_body}'.encode(), bytes.fromhex(auth_sig))
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False
    return True

def lambda_handler(event, context):
    if not verify_request_signature(event):
        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Unauthorized'}),
            'headers': {'Content-Type': 'application/json'}
        }

    body = json.loads(event['body'])
    if body.get("type") == REQUEST_TYPE.PING:
        return respond_pong()
    elif body.get("type") == REQUEST_TYPE.COMMAND:
        return handle_command(body)
    elif body.get("type") == REQUEST_TYPE.COMPONENT:
        return handle_interaction(body)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Bad Request'}),
            'headers': {'Content-Type': 'application/json'}
        }
    

def respond_pong():
    return {
        'statusCode': 200,
        'body': json.dumps({'type': INTERACTION_CALLBACK_TYPE.PONG}),
        'headers': {'Content-Type': 'application/json'}
    }

def handle_command(body):
    command_name = body["data"]["name"]
    user_id = body["member"]["user"]["id"]
    
    if command_name == "대화시작":
        return create_choice_response(user_id)
    
    # "대화시작" 커맨드 외에는 모두 같은 응답을 처리
    message = "아리가토~! 무엇을 도와줄까요? 케이트는 여러분과의 대화를 기다리고 있어요!"

    return create_response(message)
    
def create_response(message, image_url=None):
    response_body = {
        "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "tts": False,
            "content": message,
            "embeds": [],
        }
    }
    
    # 이미지 URL이 제공되면 embed에 추가
    if image_url:
        embed = {
            "image": {
                "url": image_url
            }
        }
        response_body["data"]["embeds"].append(embed)
    
    return {
        'statusCode': 200,
        'body': json.dumps(response_body),
        'headers': {'Content-Type': 'application/json'}
    }

def create_choice_response(user_id):
    return {
        'statusCode': 200,
        'body': json.dumps({
            "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": "케이트와의 첫 만남이네요! 어떻게 하실 건가요?",
                "components": [
                    {
                        "type": 1,  # ActionRow 타입
                        "components": [
                            {
                                "type": 2,  # 버튼 타입
                                "label": "친절하게 인사하기",
                                "style": 1,  # 블루 컬러 스타일
                                "custom_id": "greet"  # 버튼 클릭 시 식별할 수 있는 ID
                            },
                            {
                                "type": 2,  # 버튼 타입
                                "label": "무시하고 지나가기",
                                "style": 4,  # 레드 컬러 스타일
                                "custom_id": "ignore"  # 버튼 클릭 시 식별할 수 있는 ID
                            }
                        ]
                    }
                ]
            }
        })
    }

def handle_interaction(interaction):
    user_id = interaction["member"]["user"]["id"]
    custom_id = interaction["data"]["custom_id"]
    
    # 사용자의 선택에 따라 분기 처리
    if custom_id == "greet":
        return handle_greet_interaction(user_id)
    elif custom_id == "ignore":
        return handle_ignore_interaction(user_id)
    elif custom_id == "share_story":
        return handle_share_story_interaction(user_id)
    else:
        return create_response("알 수 없는 선택입니다. 다시 시도해주세요.")
    
    return create_response(message, image_url)
    
def handle_greet_interaction(user_id):
    score_change = 10
    message = "와우, 정말 친절한 인사네요! 케이트, 기분이 좋아졌어요. 😀"
    image_url = "https://cdn.discordapp.com/attachments/1226850480895037460/1226862880171884594/happy.jpg?ex=66265018&is=6613db18&hm=debf52d796cc7db3e593d07667c610bd044a502d9e8d661d99fab4d91ae27c67&"
    
    extra_message = update_relationship_score(user_id, score_change)
    if extra_message:
        message += "\n" + extra_message
    
    # 사용자 아이디와 현재 호감도 정보 추가
    current_score = user_states.get(user_id, 0)
    relationship_info = f"\n\n현재 사용자 ID: {user_id}\n호감도 점수: {current_score}"
    message += relationship_info

    return handle_share_story_interaction(message, image_url)
    
def handle_ignore_interaction(user_id):
    score_change = -5
    message = "오, 저를 무시하시는 건가요? 케이트가 조금 슬퍼졌어요. 😢"
    image_url = "https://media.discordapp.net/attachments/1226850480895037460/1226863974637895700/image.png?ex=6626511d&is=6613dc1d&hm=f62656f24de7d92f2b1fdef7306aa05885a21d04a62529fa1542599fd130189e&=&format=webp&quality=lossless&width=196&height=350"

    extra_message = update_relationship_score(user_id, score_change)
    if extra_message:
        message += "\n" + extra_message
    
    # 사용자 아이디와 현재 호감도 정보 추가
    current_score = user_states.get(user_id, 0)
    relationship_info = f"\n\n현재 사용자 ID: {user_id}\n호감도 점수: {current_score}"
    message += relationship_info

    return handle_share_story_interaction(message, image_url)
    
def handle_share_story_interaction(message, image_url=None):
    response_body = {
        "type": INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "tts": False,
            "content": message,
            "components": [
                {
                    "type": 1,  # ActionRow 타입
                    "components": [
                        {
                            "type": 2,  # 버튼 타입
                            "label": "더 알아보기",
                            "style": 1,  # 블루 컬러 스타일
                            "custom_id": "learn_more"
                        },
                        {
                            "type": 2,
                            "label": "이야기 나누기",
                            "style": 1,
                            "custom_id": "share_story"
                        },
                        {
                            "type": 2,
                            "label": "피드백 주기",
                            "style": 4,  # 레드 컬러 스타일
                            "custom_id": "give_feedback"
                        }
                    ]
                }
            ],
            "embeds": [],
        }
    }
    
    # 이미지 URL이 제공되면 embed에 추가
    if image_url:
        embed = {
            "image": {
                "url": image_url
            }
        }
        response_body["data"]["embeds"].append(embed)
    
    return {
        'statusCode': 200,
        'body': json.dumps(response_body),
        'headers': {'Content-Type': 'application/json'}
    }

user_states = {}

def update_relationship_score(user_id, score_change):
    current_score = user_states.get(user_id, 0) + score_change
    user_states[user_id] = current_score
    print(f"Updated relationship score for {user_id} by {score_change}. Current score: {current_score}")
    
    # 관계 점수에 따른 추가 메시지
    if current_score > 20:
        extra_message = "우리 사이가 많이 가까워진 것 같아요. 더 많은 이야기를 나누고 싶어요!"
    elif current_score < -10:
        extra_message = "좀 서운해요... 하지만 여전히 당신과 대화하고 싶어요."
    else:
        extra_message = ""
    
    return extra_message

# 사용자와의 관계 점수를 저장하고 관리하는 예제 코드를 통해, 케이트와 사용자 사이의 상호작용을 보다 세밀하게 조정할 수 있습니다. 이를 통해 사용자는 더 개인화된 대화 경험을 할 수 있게 됩니다.