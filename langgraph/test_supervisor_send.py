"""
Simple test script to send a message from Tamar via the supervisor.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from nodes.supervisor.supervisor import load_agent_personas
from telegram_exm import send_telegram_message

def test_send_message():
    """Test sending a simple message from Tamar to the group."""
    
    print("Loading agent personas...")
    personas = load_agent_personas()
    
    # Get Tamar's phone number
    tamar_persona = personas.get("active")
    if not tamar_persona:
        print("Error: Could not find active agent persona")
        return
    
    tamar_phone = tamar_persona.get("phone_number")
    tamar_name = tamar_persona.get("first_name")
    
    print(f"Found persona: {tamar_name} ({tamar_phone})")
    
    # Chat ID from config
    chat_id = "3175400700"
    
    # Send test message
    print(f"\nSending message from {tamar_name} to chat {chat_id}...")
    response = send_telegram_message(
        from_phone=tamar_phone,
        to_target=chat_id,
        content_value="hi, this is from the supervisor"
    )
    
    print(f"\nResponse: {response}")
    
    if response and response.get("success"):
        print("✅ Message sent successfully!")
    else:
        print(f"❌ Failed to send message: {response.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_send_message()
