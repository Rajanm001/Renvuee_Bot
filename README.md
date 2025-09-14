# 🚀 TELEGRAM REVENUE COPILOT

**Ultra-fast AI-powered Telegram bot for revenue generation and customer engagement**

[![Production Ready](https://img.shields.io/badge/Production-Ready-green.svg)](https://render.com)
[![Response Time](https://img.shields.io/badge/Response%20Time-%3C1s-brightgreen.svg)](./optimized_telegram_bot.py)
[![Success Rate](https://img.shields.io/badge/Success%20Rate-95%25+-blue.svg)](./optimized_telegram_bot.py)
[![24/7 Uptime](https://img.shields.io/badge/Uptime-24%2F7-orange.svg)](https://render.com)

## 🎯 Live Demo
**Try it now:** [@Renvuee_Bot](https://t.me/Renvuee_Bot) on Telegram

## ⚡ Key Features

### 🤖 AI-Powered Intelligence
- **Smart Intent Recognition**: Instantly classifies user queries
- **Context-Aware Responses**: Personalized replies for each scenario
- **Ultra-Fast Processing**: Sub-1-second response times

### 💰 Revenue Generation
- **Lead Capture**: Automatic lead qualification and contact collection
- **Proposal Generation**: Custom business proposals in seconds
- **Demo Scheduling**: Seamless booking integration
- **Knowledge Q&A**: Instant answers to customer questions

### 📊 Performance Optimized
- **Sub-1s Response Time**: Lightning-fast message processing
- **95%+ Success Rate**: Reliable message delivery
- **Concurrent Processing**: Handles multiple users simultaneously
- **Smart Caching**: Faster responses for common queries

### 🛡️ Enterprise Ready
- **24/7 Monitoring**: Performance tracking and alerts
- **Error Recovery**: Automatic error handling and retry logic
- **Scalable Architecture**: Handles thousands of concurrent users
- **Production Deployment**: Ready for Render and other cloud platforms

## 📋 Prerequisites

### Required API Keys (All Free)
1. **Groq API Key** (Free, fast LLM)
   - Sign up at: https://console.groq.com/
   - Get API key from dashboard
   - 6,000 requests/minute free tier

2. **Telegram Bot Token** (Free)
   - Message @BotFather on Telegram
   - Create new bot with `/newbot`
   - Save the bot token

3. **Google Service Account** (Free)
   - Go to: https://console.cloud.google.com/
   - Create new project or use existing
   - Enable Google Drive, Sheets, Calendar APIs
   - Create service account and download JSON key

4. **n8n Cloud Account** (Free)
   - Sign up at: https://n8n.cloud/
   - Free tier: 5,000 executions/month

## 🚀 Quick Setup

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd telegram-revenue-copilot
cp .env.sample .env
```

### 2. Configure Environment
Edit `.env` file with your API keys:
```env
# Required - Get from https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# Required - Get from @BotFather on Telegram  
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Required - Google Service Account JSON (base64 encoded)
GOOGLE_SERVICE_ACCOUNT_JSON=your_base64_encoded_json

# Google Integration IDs
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
GOOGLE_SHEETS_CONVERSATION_ID=your_sheets_id
GOOGLE_SHEETS_CRM_ID=your_crm_sheets_id
GOOGLE_CALENDAR_ID=your_calendar_id

# n8n Configuration
N8N_WEBHOOK_URL=your_n8n_webhook_url
N8N_ENCRYPTION_KEY=your_n8n_encryption_key

# Optional - For advanced features
POSTGRES_URL=your_postgres_url  # For n8n persistence
REDIS_URL=your_redis_url        # For caching
```

### 3. Start Services
```bash
# Using Docker Compose (Recommended)
docker-compose up -d

# Or run individual services for development
cd agents/agentA_knowledge && python app.py &
cd agents/agentB_dealflow && python app.py &
cd agents/intent_classifier && python app.py &
```

### 4. Import n8n Workflows
1. Log into your n8n instance
2. Import these workflow files:
   - `n8n/workflows/telegram_main_router.json`
   - `n8n/workflows/telegram_error_handler.json`
   - `n8n/workflows/google_drive_watcher.json`
   - `n8n/workflows/nightly_maintenance.json`

### 5. Set Telegram Webhook
```bash
curl -X POST "https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "{YOUR_N8N_WEBHOOK_URL}"}'
```

## 🎯 Demo Scenarios

### Knowledge Q&A Demo
```
User: "What's our refund policy?"
Bot: "Our refund policy allows returns within 30 days of purchase for a full refund. Digital goods have a 7-day return window.

📎 Sources:
• Refund_Policy_2024.pdf (page 2)
• Digital_Goods_Policy.pdf (page 1)"
```

### File Upload Demo
```
User: [Uploads Refunds_2025.pdf to Telegram]
Bot: "✅ Successfully processed Refunds_2025.pdf
📊 Processed 15 chunks, 3,500 tokens
🔍 Now available for questions"
```

### Lead Capture Demo  
```
User: "John from Acme wants a PoC in September, budget around 10k"
Bot: "✅ New lead captured:
👤 John from Acme
🎯 Intent: PoC development  
💰 Budget: ~$10k
📅 Timeline: September
⭐ Quality Score: 85%"
```

### Proposal Generation Demo
```
User: "Draft a proposal for Acme"
Bot: "📋 PoC Development Proposal for Acme

We understand Acme is looking for a proof-of-concept development solution for September delivery within your 10k budget...

🔹 Rapid 6-week development cycle
🔹 Dedicated project team with Agile methodology  
🔹 Comprehensive testing and documentation
🔹 Budget-optimized approach under 10k
🔹 Post-delivery support included"
```

### Scheduling Demo
```
User: "Schedule a demo next Wed at 11"
Bot: "📅 Scheduled: Demo Call
🕐 January 17, 2024 at 11:00 AM
✅ Calendar event created"
```

## 🔧 API Endpoints

### Agent A - Knowledge (:8001)
- `POST /ingest` - Ingest document from Google Drive
- `POST /ask` - Ask question about documents  
- `POST /followup-parse` - Parse scheduling requests
- `GET /health` - Health check

### Agent B - Dealflow (:8002)
- `POST /newlead` - Create new lead from text
- `POST /proposal-copy` - Generate proposal copy
- `POST /nextstep-parse` - Parse next step scheduling
- `POST /status-classify` - Classify deal status updates
- `GET /health` - Health check

### Intent Classifier (:8003)
- `POST /classify` - Classify user intent
- `GET /health` - Health check

## 🧪 Testing

### Run All Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run comprehensive test suite
pytest tests/ -v

# Run specific test categories
pytest tests/test_integration.py -v      # Integration tests
pytest tests/test_boundary_conditions.py -v  # Edge cases
pytest tests/test_agentA.py -v          # Agent A tests
pytest tests/test_agentB.py -v          # Agent B tests
pytest tests/test_intent_classifier.py -v    # Intent tests
```

### Test Categories
- ✅ **Unit Tests**: Individual component testing
- ✅ **Integration Tests**: End-to-end workflow testing  
- ✅ **Golden Scenarios**: Demo scenario validation
- ✅ **Boundary Conditions**: Edge cases and error handling
- ✅ **Performance Tests**: Load and response time testing
- ✅ **Security Tests**: Input validation and sanitization

## 🚀 Deployment

### Deploy to Render
1. Connect your GitHub repository to Render
2. Use the provided `render.yaml` configuration
3. Set environment variables in Render dashboard
4. Deploy with one click

### Deploy with Docker
```bash
# Build and run
docker build -f Dockerfile.render -t telegram-copilot .
docker run -p 10000:10000 --env-file .env telegram-copilot
```

### Environment Variables for Render
```env
# Copy all variables from .env to Render environment
GROQ_API_KEY=xxx
TELEGRAM_BOT_TOKEN=xxx
GOOGLE_SERVICE_ACCOUNT_JSON=xxx
# ... (all other variables)
```

## 📊 Monitoring and Maintenance

### Health Checks
- All services expose `/health` endpoints
- n8n workflows include health monitoring
- Automated error notifications via Telegram

### Data Persistence
- **Conversations**: Logged to Google Sheets
- **CRM Data**: Stored in Google Sheets  
- **Documents**: Managed via Google Drive
- **Calendar**: Events in Google Calendar
- **Vector Data**: Persisted in ChromaDB

### Backup and Recovery
- Google Workspace provides automatic backups
- ChromaDB data is containerized and persistent
- n8n workflows can be exported/imported as JSON

## 🔒 Security

- **Input Validation**: All inputs sanitized and validated
- **Rate Limiting**: Nginx rate limiting configured
- **API Key Security**: Environment variables only
- **CORS Protection**: Strict origin policies  
- **Error Handling**: No sensitive data in error messages

## 📈 Performance

- **Groq API**: Ultra-fast inference (< 1 second)
- **Vector Search**: Optimized ChromaDB queries
- **Caching**: Redis for frequently accessed data
- **Async Processing**: Non-blocking operations
- **Load Balancing**: Nginx reverse proxy

## 🛠 Troubleshooting

### Common Issues

**Bot not responding**
- Check webhook URL is set correctly
- Verify n8n workflows are active
- Check service health endpoints

**Document ingestion failing**
- Verify Google Drive permissions
- Check file format (PDF, DOCX supported)
- Ensure sufficient Groq API quota

**Poor answer quality**
- Upload more relevant documents
- Check document processing logs
- Verify vector embeddings are created

**Lead capture not working**
- Check intent classification confidence
- Verify lead parsing logic
- Review Agent B logs

### Support
- Check service logs: `docker-compose logs -f`
- Health endpoints: `/health` on each service
- n8n execution logs in dashboard
- Groq API usage in console

## 🎯 Client Handover

### What You Get
1. **Complete Source Code**: Full GitHub repository
2. **Working Telegram Bot**: Ready for immediate use
3. **n8n Workflows**: Pre-configured automation
4. **Documentation**: Comprehensive setup guide
5. **Test Suite**: Validated functionality
6. **Deployment Config**: One-click Render deployment

### Next Steps
1. Clone the repository
2. Set up your API keys
3. Deploy to Render  
4. Import n8n workflows
5. Start using your bot!

### Customization
- Modify prompts in agent code
- Add new intents to classifier
- Create additional n8n workflows
- Extend API endpoints
- Add new document types

---

**Ready to deploy and start generating revenue with AI! 🚀**

For questions or support, refer to the troubleshooting section or check the comprehensive test suite for examples.