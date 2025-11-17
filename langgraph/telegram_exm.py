import requests
import os
import json

TELEGRAM_HOST = os.environ.get('TELEGRAM_HOST', 'localhost')
TELEGRAM_PORT = os.environ.get('TELEGRAM_PORT', '4000')
TELEGRAM_API_URL = f"http://{TELEGRAM_HOST}:{TELEGRAM_PORT}"
TAMAR_NUMBER_ENCODED = "%2B37379276083"
TAMAR_NUMBER = "+37379276083"
TAMAR_API_HASH = "d6b4e90157370c68eefd02872c165541"
TAMAR_API_ID = 25872607
YAIR_PHONE_ENCODED = "%2B972584087777"
YAIR_NUMBER = "+972584087777"
MATAN_PHONE_ENCODED = "%2B1925 208 8164"
MATAN_NUMBER = "+1925 208 8164"
MATAN_API_HASH = "82efd609e785a46bb8c98cbe5052d473"
MATAN_API_ID = 34480201
PETACH_TIKVA_CHAT_ID = "3175400700"
REPLIED_MESSAGE_ID = 13

def print_response(response):
    print('Status Code:', response.status_code)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False)) 

# authentication

def send_telegram_verification_code():
    postUrl = f"{TELEGRAM_API_URL}/api/auth/send-code"
    payload = {
      "phone": TAMAR_NUMBER,
      "apiId": TAMAR_API_ID,
      "apiHash": TAMAR_API_HASH
    }
    print('Sending verification code to:', postUrl)
    response = requests.post(postUrl, json=payload)
    print_response(response)
    return response.json()

def verify_telegram_code():
    postUrl = f"{TELEGRAM_API_URL}/api/auth/verify-code"
    payload = {
      "phone": TAMAR_NUMBER,
      "code": "12345"  # Replace with the actual code received
    }
    print('Verifying code at:', postUrl)
    response = requests.post(postUrl, json=payload)
    print_response(response)
    return response.json()

# message and chat operations

def get_unread_telegram_messages(): 
    getUrl = f"{TELEGRAM_API_URL}/api/messages/unread?accountPhone={TAMAR_NUMBER_ENCODED}&target={YAIR_PHONE_ENCODED}"
    print('Fetching unread messages from:', getUrl)
    response = requests.get(getUrl)
    print_response(response)
    return response.json()

def get_all_chats():
    getUrl = f"{TELEGRAM_API_URL}/api/chats/all?accountPhone={MATAN_PHONE_ENCODED}"
    print('Fetching all chats from:', getUrl)
    response = requests.get(getUrl)
    print_response(response)
    return response.json()

def get_chat_messages():
    getUrl = f"{TELEGRAM_API_URL}/api/chat-messages?phone={TAMAR_NUMBER_ENCODED}&chatId={PETACH_TIKVA_CHAT_ID}&limit=5"
    print('Fetching messages from:', getUrl)
    response = requests.get(getUrl)
    print_response(response)
    return response.json()


def get_all_group_participants():
    """
    Fetch all participants in a group chat."""
    getUrl = f"{TELEGRAM_API_URL}/api/participants?phone={TAMAR_NUMBER_ENCODED}&chatId={PETACH_TIKVA_CHAT_ID}"
    print('Fetching all group participants from:', getUrl)
    response = requests.get(getUrl)
    print_response(response)
    return response.json()

# sending messages and replies

def send_telegram_message():
    postUrl = f"{TELEGRAM_API_URL}/api/messages/send"
    payload = {
      "fromPhone": TAMAR_NUMBER,
      "toTarget": PETACH_TIKVA_CHAT_ID,
      "content": {
        "type": "text",
        "value": "hi there from the python api!!"
      }
    }
    print('Sending message to:', postUrl)
    response = requests.post(postUrl, json=payload)
    print_response(response)
    return response.json()

def replay_to_telegram_message():
    # NOTE: every telegram account have its own message IDs although the messages are in the same chat!!
    postUrl = f"{TELEGRAM_API_URL}/api/messages/send"
    payload = {
      "fromPhone": MATAN_NUMBER,
      "toTarget": PETACH_TIKVA_CHAT_ID,
      "content": {
        "type": "text",
        "value": "This is a reply to your message from the python API."
      },
      "replyTo": REPLIED_MESSAGE_ID
    }
    print('Replying to message at:', postUrl)
    response = requests.post(postUrl, json=payload)
    print_response(response)
    return response.json()

def reply_to_telegram_message_by_timestamp():
    postUrl = f"{TELEGRAM_API_URL}/api/messages/send"
    payload = {
      "fromPhone": TAMAR_NUMBER,
      "toTarget": PETACH_TIKVA_CHAT_ID,
      "content": {
        "type": "text",
        "value": "This is a reply to your message by timestamp from the python API."
      },
      "replyToTimestamp": "2025-11-13T07:13:48.000Z"
    }
    print('Replying to message by timestamp at:', postUrl)
    response = requests.post(postUrl, json=payload)
    print_response(response)
    return response.json()



# get_unread_telegram_messages()
# get_all_chats()
# get_chat_messages()
# get_all_group_participants()
#send_telegram_message()
# replay_to_telegram_message()
# reply_to_telegram_message_by_timestamp()