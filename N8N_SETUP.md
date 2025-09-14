# 🔧 N8N WORKFLOWS SETUP GUIDE

## 📋 Complete n8n Integration for Telegram Revenue Copilot

### 🎯 Overview
These n8n workflows provide advanced automation for your Telegram bot:
- **Main Workflow**: Message processing and smart responses
- **Lead Capture**: Automatic lead scoring and CRM integration
- **Analytics**: Performance tracking and insights

---

## 🛠️ Setup Instructions

### Prerequisites
- n8n instance (cloud or self-hosted)
- Google Sheets account
- Email service (Gmail/SMTP)
- Telegram Bot Token

### Step 1: Install n8n
```bash
# Using npm
npm install n8n -g

# Using Docker
docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n

# Cloud version
# Visit https://app.n8n.cloud
```

### Step 2: Import Workflows
1. Open n8n interface (http://localhost:5678)
2. Go to "Workflows" → "Import from File"
3. Import each JSON file from `n8n_workflows/` folder:
   - `telegram_main_workflow.json`
   - `lead_capture_workflow.json`

### Step 3: Configure Credentials

#### Telegram Bot
1. Add new credential: "Telegram API"
2. Set Bot Token: `8336045140:AAH_OmqV3MMCszVbL6mOJs6zK5ADPNR2WJc`

#### Google Sheets
1. Add new credential: "Google Service Account"
2. Create service account in Google Cloud Console
3. Download JSON key file
4. Enable Google Sheets API
5. Share spreadsheet with service account email

#### Email Service
1. Add new credential: "SMTP"
2. Configure your email provider:
   - Gmail: smtp.gmail.com:587
   - Outlook: smtp-mail.outlook.com:587

### Step 4: Set Environment Variables
```
TELEGRAM_BOT_TOKEN=8336045140:AAH_OmqV3MMCszVbL6mOJs6zK5ADPNR2WJc
GOOGLE_SHEET_ID=your_spreadsheet_id_here
SALES_EMAIL=sales@renvuee.com
```

---

## 🚀 Workflow Details

### Main Telegram Workflow
**Purpose**: Process incoming messages and generate smart responses

**Features**:
- Webhook endpoint for Telegram
- Advanced intent classification
- Context-aware response generation
- Analytics logging
- Error handling

**Endpoints**:
- Webhook URL: `https://your-n8n.com/webhook/telegram-webhook`

### Lead Capture Workflow
**Purpose**: Automatic lead processing and CRM integration

**Features**:
- Lead scoring algorithm
- Contact information extraction
- CRM integration (Google Sheets)
- Sales team notifications
- Follow-up automation

**Endpoints**:
- Webhook URL: `https://your-n8n.com/webhook/lead-capture`

---

## 📊 Google Sheets Setup

### Create Required Sheets

#### Analytics Sheet
Columns:
- timestamp
- user_id
- username
- intent
- message
- response_sent

#### Leads Sheet
Columns:
- timestamp
- user_id
- username
- intent
- lead_score
- emails
- phones
- companies
- message
- status
- source

### Sample Formulas
```
# Lead conversion rate
=COUNTIF(H:H,"converted")/COUNTA(H:H)*100

# Average lead score
=AVERAGE(E:E)

# Daily message count
=COUNTIF(A:A,TODAY())
```

---

## ⚙️ Workflow Configuration

### Message Processing
```javascript
// Intent classification patterns
const patterns = {
  greeting: /\b(hi|hello|hey|start)\b/i,
  demo_request: /\b(demo|trial|show)\b/i,
  pricing_inquiry: /\b(price|pricing|cost)\b/i,
  // ... more patterns
};
```

### Lead Scoring Algorithm
```javascript
function calculateLeadScore(intent, hasEmail, hasPhone, hasCompany) {
  let score = 0;
  
  const intentScores = {
    demo_request: 80,
    pricing_inquiry: 70,
    lead_info: 90,
    // ... more scoring
  };
  
  score += intentScores[intent] || 30;
  if (hasEmail) score += 15;
  if (hasPhone) score += 10;
  if (hasCompany) score += 5;
  
  return Math.min(score, 100);
}
```

---

## 🧪 Testing Workflows

### Test Main Workflow
```bash
# Send test webhook
curl -X POST https://your-n8n.com/webhook/telegram-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {"id": 12345},
      "from": {"username": "testuser"},
      "text": "Hello"
    }
  }'
```

### Test Lead Capture
```bash
# Send test lead data
curl -X POST https://your-n8n.com/webhook/lead-capture \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 12345,
    "username": "testuser",
    "intent": "demo_request",
    "message_text": "I want a demo for my company test@email.com"
  }'
```

---

## 📈 Monitoring & Analytics

### Built-in Metrics
- Message processing rate
- Lead conversion rate
- Response time analytics
- Error rate monitoring
- User engagement metrics

### Custom Dashboards
Create Google Sheets charts for:
- Daily/weekly message volume
- Intent distribution
- Lead score trends
- Conversion funnel analysis

---

## 🔧 Customization

### Add New Intents
1. Update intent classification patterns
2. Add response templates
3. Update lead scoring rules
4. Test thoroughly

### Integrate with CRM
Replace Google Sheets with:
- HubSpot API
- Salesforce API
- Pipedrive API
- Custom database

### Add Notifications
- Slack notifications
- Discord webhooks
- SMS alerts via Twilio
- Push notifications

---

## 🐛 Troubleshooting

### Common Issues

#### Webhook Not Receiving Data
- Check webhook URL configuration
- Verify Telegram webhook setup
- Check n8n logs for errors

#### Google Sheets Permission Error
- Verify service account has access
- Check spreadsheet sharing settings
- Validate credentials

#### Email Notifications Not Sending
- Check SMTP configuration
- Verify credentials
- Test email connectivity

### Debug Mode
1. Enable workflow logging
2. Check execution history
3. Review error messages
4. Test individual nodes

---

## 🚀 Production Deployment

### Security Checklist
- [ ] Secure webhook endpoints
- [ ] Encrypt sensitive credentials
- [ ] Enable rate limiting
- [ ] Set up monitoring alerts
- [ ] Regular backup of workflows

### Performance Optimization
- [ ] Enable workflow caching
- [ ] Optimize large data processing
- [ ] Set appropriate timeouts
- [ ] Monitor resource usage

---

**🎉 Your n8n workflows are now ready for production!**

These workflows provide:
- ✅ Automated message processing
- ✅ Smart lead capture and scoring
- ✅ CRM integration
- ✅ Performance analytics
- ✅ Sales team notifications
- ✅ Error handling and recovery

**Next Steps:**
1. Import all workflows
2. Configure credentials
3. Test thoroughly
4. Deploy to production
5. Monitor performance