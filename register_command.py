import requests

from dataclasses import dataclass

from time import sleep


@dataclass
class APPLICATION_COMMAND_OPTION_TYPE:
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    ATTACHMENT = 11


APPLICATION_ID = '<your application id here>'

BOT_TOKEN = '<your bot token here>'

HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}

# https://discord.com/developers/docs/interactions/slash-commands#registering-a-command
global_url = f"https://discord.com/api/v8/applications/{APPLICATION_ID}/commands"


def publish_command(url, commands):
    r = requests.post(url, headers=HEADERS, json=commands)
    if r.status_code != 200:
        # 재시도
        sleep(20)
        print(f"Post to {url} failed; retrying once")
        r = requests.post(url, headers=HEADERS, json=commands)

    # 디버그용
    print(f"Response from {url}: {r.text}")

def get_all_commands(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"Failed to fetch commands with status code {r.status_code}")
        return []

def delete_command(command_id):
    url = f"https://discord.com/api/v8/applications/{APPLICATION_ID}/commands/{command_id}"
    r = requests.delete(url, headers=HEADERS)
    if r.status_code == 204:
        print(f"Command {command_id} deleted successfully")
    else:
        print(f"Failed to delete command {command_id}: {r.text}")

def run_delete():
    existing_commands = get_all_commands(global_url)
    for command in existing_commands:
        if command['name'] != '대화시작':  # '대화시작' 커맨드를 제외하고 삭제
            delete_command(command['id'])

def run():
    commands = [
        {
            "name": "테스트",
            "description": "임시 테스트 명령어입니다.",
        }
    ]
    for command in commands:
        publish_command(global_url, command)
        print()

    print(f"{len(commands)} published")


if __name__ == "__main__":
    run_delete()