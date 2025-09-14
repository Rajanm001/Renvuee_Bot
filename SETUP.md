# 🚀 LOCAL SETUP GUIDE

## 📋 Complete Installation Guide for Ultimate Telegram Revenue Copilot

### 🎯 Prerequisites

#### Required Software
- **Python 3.8+** (Download from [python.org](https://python.org))
- **Git** (Download from [git-scm.com](https://git-scm.com))
- **Text Editor** (VS Code, PyCharm, or any editor)

#### Required Accounts
- **Telegram Account** (for testing)
- **Telegram Bot Token** (get from @BotFather)

---

## 🛠️ Step-by-Step Installation

### Step 1: Clone Repository
```bash
# Clone the repository
git clone https://github.com/Rajanm001/Renvuee_Bot.git
cd Renvuee_Bot
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Get Telegram Bot Token
1. Open Telegram and search for `@BotFather`
2. Start a conversation with `/start`
3. Create new bot with `/newbot`
4. Choose a name and username for your bot
5. Copy the bot token provided

### Step 4: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your token
# TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Step 5: Test Installation
```bash
# Run the test suite
python test_suite.py

# If all tests pass, start the bot
python main.py
```

---

## 🎮 Running the Bot

### Local Development
```bash
# Start the ultimate bot
python ultimate_bot.py
```

### Production Mode
```bash
# Start with production launcher
python main.py
```

### Testing Mode
```bash
# Run comprehensive tests
python test_suite.py
```

---

## 🔧 Configuration Options

### Environment Variables
```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional
LOG_LEVEL=INFO
ENVIRONMENT=development
CACHE_SIZE=1000
MAX_WORKERS=15
```

### Bot Customization

#### Update Knowledge Base
Edit `ultimate_bot.py` and modify the `knowledge_base` dictionary:
```python
self.knowledge_base = {
    "pricing": {
        "title": "Your Custom Title",
        "content": "Your custom content here..."
    }
}
```

#### Customize Menus
Edit the `menus` dictionary in `ultimate_bot.py`:
```python
self.menus = {
    "main": {
        "title": "Your Bot Title",
        "options": ["Option 1", "Option 2", ...]
    }
}
```

---

## 🧪 Testing Your Setup

### Quick Tests
```bash
# Test bot connection
python -c "from ultimate_bot import UltimateTelegramBot; bot = UltimateTelegramBot('your_token'); print('✅ Bot configured correctly')"

# Run unit tests
python -m unittest test_suite.TestUltimateTelegramBot.test_01_bot_initialization

# Full test suite
python test_suite.py
```

### Manual Testing
1. Start your bot: `python main.py`
2. Open Telegram
3. Search for your bot by username
4. Send `/start` to begin conversation
5. Test different message types:
   - "Hello" (greeting)
   - "Show me pricing" (pricing inquiry)
   - "I want a demo" (demo request)
   - "I need help" (support)

---

## 🐛 Troubleshooting

### Common Issues

#### "Module not found" error
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### Bot not responding
1. Check bot token is correct in `.env`
2. Ensure bot is started correctly
3. Check logs for error messages
4. Verify internet connection

#### Permission errors
```bash
# On Windows, run as administrator
# On macOS/Linux, check file permissions
chmod +x main.py
```

#### Port already in use
```bash
# Find and kill existing Python processes
# Windows:
taskkill /f /im python.exe
# macOS/Linux:
pkill python
```

### Debug Mode
```bash
# Run with verbose logging
LOG_LEVEL=DEBUG python main.py

# Check log file
cat bot.log
```

---

## 📱 Bot Features Testing

### Test All Features
```bash
# Interactive test script
python -c "
import json
from ultimate_bot import UltimateTelegramBot

bot = UltimateTelegramBot('your_token')

# Test menu generation
menu = bot.menus['main']
print('Main menu:', json.dumps(menu, indent=2))

# Test intent classification
from ultimate_bot import UserSession
session = UserSession(12345, 'testuser')
intent, confidence, patterns = bot.classify_intent_advanced('show me pricing', session)
print(f'Intent: {intent}, Confidence: {confidence}')

# Test response generation
response, keyboard = bot.generate_smart_response('hello', 'greeting', session)
print('Response generated successfully')

print('✅ All components working correctly!')
"
```

### Test Scenarios
1. **Greeting Flow**: Send "Hello" → Check main menu appears
2. **Pricing Inquiry**: Send "What's your pricing?" → Check pricing info
3. **Demo Request**: Send "I want a demo" → Check demo options
4. **Support Request**: Send "I need help" → Check support info
5. **Lead Capture**: Send "I'm interested" → Check lead form

---

## 🚀 Performance Optimization

### For High Traffic
```python
# In ultimate_bot.py, increase worker threads
self.executor = ThreadPoolExecutor(max_workers=25)

# Enable response caching
# Already implemented in the bot
```

### Memory Management
```bash
# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

---

## 📊 Monitoring & Metrics

### Built-in Metrics
The bot automatically tracks:
- Total users
- Messages processed
- Response times
- Success rates
- Leads captured
- Demos scheduled

### View Live Metrics
```python
# Check metrics while bot is running
from ultimate_bot import UltimateTelegramBot
bot = UltimateTelegramBot('your_token')
bot.log_performance_enhanced()
```

---

## 🔄 Updates & Maintenance

### Update Bot
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run tests
python test_suite.py

# Restart bot
python main.py
```

### Backup Configuration
```bash
# Backup your customizations
cp .env .env.backup
cp ultimate_bot.py ultimate_bot.py.backup
```

---

## 💡 Development Tips

### Custom Features
1. Add new intents in `classify_intent_advanced()`
2. Create responses in `generate_smart_response()`
3. Update knowledge base with your content
4. Add new menu options as needed

### Best Practices
- Always test changes with `test_suite.py`
- Keep bot token secure (never commit to git)
- Monitor logs for errors
- Regular backups of customizations

---

## 📞 Support

If you encounter issues:

1. **Check Logs**: Look at `bot.log` for errors
2. **Run Tests**: Execute `python test_suite.py`
3. **Documentation**: Read this guide thoroughly
4. **GitHub Issues**: Create an issue in the repository

---

**🎉 You're ready to run the Ultimate Telegram Revenue Copilot!**

The bot includes:
- ✅ Smart conversation flows
- ✅ Interactive menus  
- ✅ Lead capture system
- ✅ Performance monitoring
- ✅ Comprehensive testing
- ✅ Error handling

**Next Steps:**
1. Customize the bot for your business
2. Test thoroughly with real users
3. Deploy to production (see DEPLOY.md)
4. Monitor performance and optimize