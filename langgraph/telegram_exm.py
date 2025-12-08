import requests
import os
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

TELEGRAM_HOST = os.environ.get('TELEGRAM_HOST', 'localhost')
TELEGRAM_PORT = os.environ.get('TELEGRAM_PORT', '4000')
TELEGRAM_API_URL = f"http://{TELEGRAM_HOST}:{TELEGRAM_PORT}"

# Test constants (for standalone testing)
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
PETACH_TIKVA_CHAT_ID = "3389864729"
REPLIED_MESSAGE_ID = 13

def print_response(response):
    """Print response for debugging."""
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

def get_unread_telegram_messages(account_phone=None, target_phone=None, chat_id=None): 
    """
    Fetch unread messages from Telegram API.
    
    Args:
        account_phone: Account phone number (will be URL encoded)
        target_phone: Target phone number for direct messages (will be URL encoded)
        chat_id: Chat ID for group chats (use this OR target_phone, not both)
    
    Returns:
        JSON response with unread messages
    """
    account_phone = account_phone or TAMAR_NUMBER
    account_encoded = account_phone.replace("+", "%2B")
    
    # Use chat_id if provided, otherwise fall back to target_phone
    if chat_id:
        getUrl = f"{TELEGRAM_API_URL}/api/messages/unread?accountPhone={account_encoded}&target={chat_id}"
    else:
        target_phone = target_phone or YAIR_NUMBER
        target_encoded = target_phone.replace("+", "%2B")
        getUrl = f"{TELEGRAM_API_URL}/api/messages/unread?accountPhone={account_encoded}&target={target_encoded}"
    
    logger.info(f'Fetching unread messages from: {getUrl}')
    
    try:
        response = requests.get(getUrl, timeout=10)
        response.raise_for_status()
        logger.info(f"Unread messages fetched successfully. Status: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching unread messages: {e}")
        return {"success": False, "error": str(e)}

def get_all_chats(account_phone=None):
    """
    Get all chats for a specific account.
    
    Args:
        account_phone: Account phone number (will be URL encoded)
    
    Returns:
        JSON response with all chats
    """
    account_phone = account_phone or TAMAR_NUMBER
    account_encoded = account_phone.replace("+", "%2B")
    
    getUrl = f"{TELEGRAM_API_URL}/api/chats/all?accountPhone={account_encoded}"
    logger.info(f'Fetching all chats from: {getUrl}')
    
    try:
        response = requests.get(getUrl, timeout=10)
        response.raise_for_status()
        logger.info(f"Chats fetched successfully. Status: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching chats: {e}")
        return {"success": False, "error": str(e)}

def get_chat_messages(phone=None, chat_id=None, limit=100):
    """
    Fetch chat messages from Telegram API.
    
    Args:
        phone: Phone number to fetch messages for (will be URL encoded)
        chat_id: Chat ID to fetch messages from
        limit: Maximum number of messages to fetch
    
    Returns:
        JSON response with chat messages
    """
    phone = phone or TAMAR_NUMBER
    chat_id = chat_id or PETACH_TIKVA_CHAT_ID
    phone_encoded = phone.replace("+", "%2B")
    
    getUrl = f"{TELEGRAM_API_URL}/api/chat-messages?phone={phone_encoded}&chatId={chat_id}&limit={limit}"
    logger.info(f'Fetching messages from: {getUrl}')
    
    try:
        response = requests.get(getUrl, timeout=10)
        response.raise_for_status()
        logger.info(f"Messages fetched successfully. Count: {response.json().get('messagesCount', 0)}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching chat messages: {e}")
        return {"success": False, "error": str(e)}


def get_all_group_participants(phone=None, chat_id=None):
    """
    Fetch all participants in a group chat.
    
    Args:
        phone: Phone number to use for request (will be URL encoded)
        chat_id: Chat ID to get participants from
    
    Returns:
        JSON response with group participants
    """
    phone = phone or TAMAR_NUMBER
    chat_id = chat_id or PETACH_TIKVA_CHAT_ID
    phone_encoded = phone.replace("+", "%2B")
    
    getUrl = f"{TELEGRAM_API_URL}/api/participants?phone={phone_encoded}&chatId={chat_id}"
    logger.info(f'Fetching all group participants from: {getUrl}')
    
    try:
        response = requests.get(getUrl, timeout=10)
        response.raise_for_status()
        logger.info(f"Group participants fetched successfully. Status: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching group participants: {e}")
        return {"success": False, "error": str(e)}

# sending messages and replies

def send_telegram_message(from_phone=None, to_target=None, content_value=None, reply_to_message_id=None, reply_to_timestamp=None):
    """
    Send a message to Telegram.
    
    Args:
        from_phone: Phone number to send from
        to_target: Target chat ID or phone number
        content_value: Message text content
        reply_to_message_id: Optional message ID to reply to
        reply_to_timestamp: Optional timestamp to reply to (alternative to message ID)
    
    Returns:
        JSON response from Telegram API
    """
    from_phone = from_phone or TAMAR_NUMBER
    to_target = to_target or PETACH_TIKVA_CHAT_ID
    content_value = content_value or "Test message from Python API"
    
    postUrl = f"{TELEGRAM_API_URL}/api/messages/send"
    payload = {
        "fromPhone": from_phone,
        "toTarget": to_target,
        "content": {
            "type": "text",
            "value": content_value
        }
    }
    
    # Add reply parameters if provided
    if reply_to_message_id:
        payload["replyTo"] = reply_to_message_id
    elif reply_to_timestamp:
        payload["replyToTimestamp"] = reply_to_timestamp
    
    logger.info(f'Sending message from {from_phone} to {to_target}')
    
    try:
        response = requests.post(postUrl, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Message sent successfully. Status: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error sending message: {e}")
        return {"success": False, "error": str(e)}

def reply_to_telegram_message(from_phone=None, to_target=None, content_value=None, reply_to_id=None):
    """
    Reply to a specific message (deprecated - use send_telegram_message with reply_to_message_id).
    
    NOTE: Every telegram account has its own message IDs although messages are in the same chat!
    """
    from_phone = from_phone or MATAN_NUMBER
    to_target = to_target or PETACH_TIKVA_CHAT_ID
    content_value = content_value or "This is a reply to your message from the python API."
    reply_to_id = reply_to_id or REPLIED_MESSAGE_ID
    
    return send_telegram_message(
        from_phone=from_phone,
        to_target=to_target,
        content_value=content_value,
        reply_to_message_id=reply_to_id
    )
 
def reply_to_telegram_message_by_timestamp(from_phone=None, to_target=None, content_value=None, reply_timestamp=None):
    """
    Reply to a message by timestamp (deprecated - use send_telegram_message with reply_to_timestamp).
    """
    from_phone = from_phone or MATAN_NUMBER
    to_target = to_target or PETACH_TIKVA_CHAT_ID
    content_value = content_value 
    reply_timestamp = reply_timestamp 
    
    return send_telegram_message(
        from_phone=from_phone,
        to_target=to_target,
        content_value=content_value,
        reply_to_timestamp=reply_timestamp
    )

def show_typing_indicator(phone, chatId, duration):
    """Show typing indicator for (duration/1000) seconds in the chat."""
    postUrl = f"{TELEGRAM_API_URL}/api/typing"
    payload = {
        "phone": phone,
        "chatId": chatId,
        "duration": duration  
    }
    print('Showing typing indicator at:', postUrl)
    response = requests.post(postUrl, json=payload)
    print_response(response)
    return response.json()

def add_reaction_to_message(phone=None, chat_id=None, message_timestamp=None, emoji=None):
    """
    Add emoji reaction to a message by timestamp.
    
    Args:
        phone: Phone number to react from
        chat_id: Chat ID where the message is
        message_timestamp: ISO timestamp of the message to react to
        emoji: Emoji to use as reaction (e.g., "👍", "❤️", "🔥")
    
    Returns:
        JSON response from Telegram API
    """
    phone = phone 
    chat_id = chat_id 
    emoji = emoji 
    
    if not message_timestamp:
        raise ValueError("message_timestamp is required")
    
    postUrl = f"{TELEGRAM_API_URL}/api/reactions"
    payload = {
        "phone": phone,
        "chatId": chat_id,
        "messageTimestamp": message_timestamp,
        "emoji": emoji
    }
    response = requests.post(postUrl, json=payload)
    print_response(response)
    return response.json()


# get_unread_telegram_messages()
# get_all_chats()
# output = get_chat_messages(phone=TAMAR_NUMBER, chat_id=PETACH_TIKVA_CHAT_ID, limit=5)
# get_all_group_participants(phone="+37379276083", chat_id="3389864729")
#send_telegram_message()
# reply_to_telegram_message()
# reply_to_telegram_message_by_timestamp()
# print(output)

# if __name__ == "__main__":
    # import time
    
    # Show typing indicator
    # show_typing_indicator(phone=TAMAR_NUMBER, chatId=PETACH_TIKVA_CHAT_ID, duration=6000)
    # add_reaction_to_message(phone=TAMAR_NUMBER, chat_id=PETACH_TIKVA_CHAT_ID, message_timestamp="2025-11-24T14:07:40.000Z", emoji="👌")
    # Wait for typing to show before sending message
    # time.sleep(6)  # Wait 6 seconds to see the typing indicator
    # output = get_chat_messages(phone=TAMAR_NUMBER, chat_id=PETACH_TIKVA_CHAT_ID, limit=5)
    # print(json.dumps(output, indent=2, ensure_ascii=False))
    # Send message
    # send_telegram_message( from_phone=TAMAR_NUMBER, to_target=PETACH_TIKVA_CHAT_ID, content_value="Hello from LangGraph Telegram EXM!" )
    # output = get_all_group_participants(phone="+37379276083", chat_id="3389864729")
    # output = get_chat_messages(phone=TAMAR_NUMBER, chat_id=PETACH_TIKVA_CHAT_ID, limit=12)
    # output['messages']
    # for msg in output['messages']:
    #     # print(msg['replyToMessageId'])
    #     if msg['replyToMessageId']:
    #         for replied_msg in output['messages']:
    #             # print(replied_msg)

    #             if replied_msg['id'] == msg['replyToMessageId']:
    #                 print(f"type of id is: {type(replied_msg['id'])} and type of replyToMessageId is: {type(msg['replyToMessageId'])}")
    #                 print("---- Replied to message ----")
    #                 print("Original message:")
    #                 print(json.dumps(replied_msg, indent=2, ensure_ascii=False))
    #                 print("The Reply message:")
    #                 name = msg["senderFirstName"] + " " + msg["senderLastName"]
    #                 print(msg['text'], " - by", name, "at", msg['date'])


        
    # print(json.dumps(output, indent=2, ensure_ascii=False))
if __name__ == "__main__":
    print(f"Fetching chats for Tamar ({TAMAR_NUMBER})...")
    
    # 1. Fetch all chats for Tamar's account
    chats_data = get_all_chats(account_phone=TAMAR_NUMBER)
    
    # 2. Check if the response is a valid list
    if isinstance(chats_data, list):
        print("\n" + "="*50)
        print("FOUND CHATS LIST:")
        print("="*50)
        
        found_target = False
        
        for chat in chats_data:
            # Extract title and ID safely
            chat_title = chat.get('title') or chat.get('username') or "Unknown"
            chat_id = chat.get('id')
            
            # Print readable output for manual inspection
            print(f"ID: {chat_id} | Name: {chat_title}")
            
            # 3. Specific check for the Samsung group
            # We look for "Samsung" in the title to highlight the target
            if "Samsung" in str(chat_title):
                found_target = True
                print(f"\n>>> 🎯 FOUND POTENTIAL MATCH: {chat_title}")
                print(f">>> USE THIS ID: {chat_id}\n")
                
        print("="*50)
        
        if not found_target:
            print("⚠️ WARNING: Could not find a group with 'Samsung' in the title.")
            print("Please check the full list above manually.")
            
    else:
        # Handle API errors
        print("Error fetching chats:")
        print(json.dumps(chats_data, indent=2, ensure_ascii=False))