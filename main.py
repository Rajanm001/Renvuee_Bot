#!/usr/bin/env python3
"""
🚀 PRODUCTION TELEGRAM BOT LAUNCHER
==================================
Single-file production bot for Render deployment
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the production bot
from production_bot import ProductionTelegramBot, logger

def main():
    """Production launcher with environment variable support"""
    
    # Get token from environment or use hardcoded for immediate deployment
    token = os.getenv('TELEGRAM_BOT_TOKEN', '8336045140:AAH_OmqV3MMCszVbL6mOJs6zK5ADPNR2WJc')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)
    
    logger.info("Starting Production Telegram Revenue Copilot")
    logger.info("Bot: @Renvuee_Bot")
    logger.info("Environment: Production")
    
    # Create and run bot
    bot = ProductionTelegramBot(token)
    bot.run()

if __name__ == "__main__":
    main()