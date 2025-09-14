# 🔑 FREE API SETUP GUIDE

## Step 1: Get Groq API Key (FREE - 6,000 requests/minute!)

1. Go to: **https://console.groq.com/**
2. Click "Sign Up" or "Sign In"
3. Verify your email
4. Go to "API Keys" in the dashboard
5. Click "Create API Key"
6. Name it "Telegram Bot"
7. Copy the API key (starts with `gsk_`)

## Step 2: Create Telegram Bot (FREE)

1. Open Telegram app on your phone/computer
2. Search for: **@BotFather**
3. Start a chat and send: `/newbot`
4. Choose a name for your bot (e.g., "Revenue Assistant")
5. Choose a username (must end with "bot", e.g., "myrevenue_bot")
6. Copy the bot token (long string with numbers and letters)
7. Send `/setdescription` and add: "AI Revenue Copilot - Document Q&A and Lead Management"

## Step 3: Create Google Service Account (FREE)

1. Go to: **https://console.cloud.google.com/**
2. Create new project or select existing one
3. Enable these APIs:
   - Google Drive API
   - Google Sheets API  
   - Google Calendar API
4. Go to "IAM & Admin" > "Service Accounts"
5. Click "Create Service Account"
6. Name: "Telegram Bot Service"
7. Click "Create and Continue"
8. Skip role assignment for now
9. Click "Done"
10. Click on your service account email
11. Go to "Keys" tab
12. Click "Add Key" > "Create New Key" > "JSON"
13. Download the JSON file

## Step 4: Base64 Encode the JSON

**On Windows (PowerShell):**
```powershell
$content = Get-Content "path\to\your\service-account.json" -Raw
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($content))
Write-Output $encoded
```

**Online Tool (easier):**
1. Go to: https://www.base64encode.org/
2. Copy your JSON file content
3. Paste and click "Encode"
4. Copy the encoded result

## Step 5: Create Google Drive Folder

1. Go to: **https://drive.google.com/**
2. Create new folder called "Telegram Bot Documents"
3. Right-click folder > "Share"
4. Add your service account email (from step 3) as Editor
5. Copy the folder ID from URL (long string after /folders/)

## Step 6: Create Google Sheets

**Conversation Log Sheet:**
1. Go to: **https://sheets.google.com/**
2. Create new sheet named "Conversation Log"
3. Add headers: Timestamp, User, Intent, Input, Output, Confidence, Citations
4. Share with service account as Editor
5. Copy sheet ID from URL

**CRM Sheet:**
1. Create another sheet named "CRM Data"
2. Add headers: Timestamp, Lead ID, Name, Company, Intent, Budget, Stage, Quality Score
3. Share with service account as Editor
4. Copy sheet ID from URL

## Step 7: Get Calendar ID

1. Go to: **https://calendar.google.com/**
2. Click "+" next to "Other calendars"
3. Choose "Create new calendar"
4. Name: "Bot Scheduled Events"
5. Click "Create calendar"
6. Go to calendar settings > "Integrate calendar"
7. Copy the Calendar ID (usually your email)

## Step 8: Sign up for n8n (FREE)

1. Go to: **https://n8n.cloud/**
2. Sign up for free account
3. Create new workflow
4. Add "Webhook" trigger node
5. Copy the webhook URL
6. Save the workflow

## Step 9: Update .env File

Edit your `.env` file with your keys:

```env
# Replace these with your actual values:
GROQ_API_KEY=gsk_your_groq_key_here
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF1234567890abcdef1234567890
GOOGLE_SERVICE_ACCOUNT_JSON=eyJ0eXBlIjoic2VydmljZV9hY2NvdW50Iiwi...your_base64_encoded_json...
GOOGLE_DRIVE_FOLDER_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
GOOGLE_SHEETS_CONVERSATION_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
GOOGLE_SHEETS_CRM_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
GOOGLE_CALENDAR_ID=your.email@gmail.com
N8N_WEBHOOK_URL=https://your-n8n-instance.app.n8n.cloud/webhook/telegram
```

## Step 10: Test Everything

```bash
python test_system.py
```

All APIs should show ✅ success!

---

## 🚀 WHAT YOU GET FOR FREE:

- **Groq API**: 6,000 requests/minute (ultra-fast LLM)
- **Telegram Bot**: Unlimited messages  
- **Google Workspace**: 15GB storage
- **n8n Cloud**: 5,000 workflow executions/month
- **HuggingFace**: Free embeddings and models

**Total cost: $0/month** 💰

This setup can handle:
- 100+ conversations per day
- Document uploads and Q&A
- Lead capture and proposals
- Calendar scheduling
- CRM data tracking

Perfect for small to medium businesses!

---

Need help? The system will guide you through any missing steps! 🤖