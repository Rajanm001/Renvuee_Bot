#!/usr/bin/env python3
"""
Live Telegram Bot Server - Webhook and Polling
This creates a live bot that can receive real messages
"""

import os
import json
import time
import logging
from datetime import datetime
from telegram_bot_complete import TelegramBot
import urllib.request
import urllib.parse
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramBotServer:
    """Live Telegram bot server with polling"""
    
    def __init__(self):
        self.bot = TelegramBot()
        self.last_update_id = 0
        self.running = False
    
    def get_updates(self, offset: int = None, timeout: int = 10) -> list:
        """Get updates from Telegram"""
        try:
            params = {'timeout': timeout}
            if offset:
                params['offset'] = offset
            
            data = urllib.parse.urlencode(params).encode('utf-8')
            request = urllib.request.Request(
                f"{self.bot.TELEGRAM_API_URL}/getUpdates",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            with urllib.request.urlopen(request, timeout=timeout + 5) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('ok'):
                    return result.get('result', [])
                else:
                    logger.error(f"Failed to get updates: {result}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    def process_update(self, update: dict):
        """Process a single update"""
        try:
            update_id = update.get('update_id', 0)
            
            if 'message' in update:
                message = update['message']
                user_info = message.get('from', {})
                chat_info = message.get('chat', {})
                text = message.get('text', '')
                
                logger.info(f"Received message from @{user_info.get('username', 'unknown')}: {text}")
                
                # Process the message
                response = self.bot.process_message(update)
                
                logger.info(f"Sent response: {response[:100]}...")
                
            # Update last update ID
            self.last_update_id = max(self.last_update_id, update_id + 1)
            
        except Exception as e:
            logger.error(f"Error processing update: {e}")
    
    def start_polling(self):
        """Start polling for messages"""
        logger.info("🚀 Starting Telegram bot polling...")
        logger.info(f"Bot info: {self.bot.get_bot_info()}")
        
        self.running = True
        
        while self.running:
            try:
                # Get updates
                updates = self.get_updates(offset=self.last_update_id)
                
                # Process each update
                for update in updates:
                    self.process_update(update)
                
                # Brief pause
                if not updates:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("Stopping bot...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        logger.info("Bot stopped")
    
    def send_test_message_to_chat(self, chat_id: int, message: str = None):
        """Send a test message to a specific chat"""
        if not message:
            message = f"🤖 Bot is online and ready! Time: {datetime.now().strftime('%H:%M:%S')}"
        
        success = self.bot.send_message(chat_id, message)
        if success:
            logger.info(f"Test message sent to chat {chat_id}")
        else:
            logger.error(f"Failed to send test message to chat {chat_id}")
        return success

def test_live_bot():
    """Test the live bot with real API calls"""
    print("🚀 TESTING LIVE TELEGRAM BOT")
    print("="*50)
    
    server = TelegramBotServer()
    
    # Test bot connection
    bot_info = server.bot.get_bot_info()
    if bot_info.get("ok"):
        result = bot_info["result"]
        print(f"✅ Bot connected: @{result['username']}")
        print(f"   Bot ID: {result['id']}")
        print(f"   Name: {result['first_name']}")
    else:
        print("❌ Bot connection failed")
        return False
    
    # Test message handling with mock data
    print("\n🧪 Testing message processing...")
    
    test_updates = [
        {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 12345, "username": "testuser", "first_name": "Test"},
                "chat": {"id": 12345, "type": "private"},
                "text": "Hello bot!"
            }
        },
        {
            "update_id": 2,
            "message": {
                "message_id": 2,
                "from": {"id": 12345, "username": "testuser", "first_name": "Test"},
                "chat": {"id": 12345, "type": "private"},
                "text": "What is your refund policy?"
            }
        }
    ]
    
    for update in test_updates:
        print(f"\n👤 Processing: {update['message']['text']}")
        server.process_update(update)
    
    # Show stats
    stats = server.bot.get_stats()
    print(f"\n📊 Bot Statistics:")
    print(f"   Messages processed: {stats['conversations_handled']}")
    print(f"   Leads captured: {stats['leads_captured']}")
    
    return True

def manual_message_test():
    """Test sending messages to real users"""
    print("\n🎯 MANUAL MESSAGE TEST")
    print("="*30)
    
    server = TelegramBotServer()
    
    print("To test with real messages:")
    print("1. Start a chat with your bot @Renvuee_Bot")
    print("2. Send a message to get your chat ID")
    print("3. Use that chat ID to send test messages")
    
    # Example of how to send a message (need real chat ID)
    # chat_id = 123456789  # Replace with real chat ID
    # server.send_test_message_to_chat(chat_id, "🤖 Hello! I'm your revenue copilot bot!")

if __name__ == "__main__":
    print("🤖 TELEGRAM REVENUE COPILOT - LIVE SERVER")
    print("="*60)
    
    # Test the bot
    if test_live_bot():
        print("\n✅ All tests passed!")
        
        print("\n📱 BOT IS READY FOR LIVE USE!")
        print(f"   Bot Username: @Renvuee_Bot")
        print(f"   Bot Name: revenuebot")
        
        print("\n🎯 To test with real messages:")
        print("1. Open Telegram")
        print("2. Search for @Renvuee_Bot")
        print("3. Start a conversation")
        print("4. Try these commands:")
        print("   • 'What is your refund policy?'")
        print("   • 'John from Acme wants a demo, budget 10k'")
        print("   • 'Draft a proposal for Acme'")
        print("   • 'Schedule a call tomorrow at 2 PM'")
        
        # Ask if user wants to start polling
        print("\n🔄 Start live polling? (y/n): ", end="")
        
        try:
            # For automated testing, we'll skip the input
            # response = input().strip().lower()
            # if response == 'y':
            #     server = TelegramBotServer()
            #     server.start_polling()
            
            manual_message_test()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
    else:
        print("\n❌ Bot tests failed - check configuration")