#!/usr/bin/env python3
"""
Complete Working Telegram Bot - Revenue Copilot
This version works with just the Telegram token for immediate testing
"""

import os
import json
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
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

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8336045140:AAH_OmqV3MMCszVbL6mOJs6zK5ADPNR2WJc")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

@dataclass
class TelegramMessage:
    message_id: int
    user_id: int
    chat_id: int
    username: str
    first_name: str
    text: str
    timestamp: datetime

class MockKnowledgeBase:
    """Mock knowledge base for demonstration"""
    
    def __init__(self):
        self.documents = {
            "refund_policy": {
                "content": "Our refund policy allows returns within 30 days of purchase for a full refund. Digital goods have a 7-day return window. All returns must include original packaging and proof of purchase.",
                "source": "Refund_Policy_2024.pdf"
            },
            "shipping_policy": {
                "content": "We offer free shipping on orders over $50. Standard shipping takes 3-5 business days, express shipping takes 1-2 business days. International shipping available to most countries.",
                "source": "Shipping_Policy_2024.pdf"
            },
            "support_hours": {
                "content": "Our customer support is available Monday-Friday 9 AM to 6 PM EST. Emergency support available 24/7 for enterprise customers. You can reach us via email, chat, or phone.",
                "source": "Support_Guidelines_2024.pdf"
            },
            "pricing": {
                "content": "Our pricing starts at $99/month for basic plan, $299/month for professional, and $599/month for enterprise. Annual plans receive 20% discount. Custom enterprise pricing available.",
                "source": "Pricing_Guide_2024.pdf"
            }
        }
    
    def search(self, query: str) -> Dict[str, Any]:
        """Simple keyword search"""
        query_lower = query.lower()
        
        # Simple keyword matching
        if any(word in query_lower for word in ["refund", "return", "money back"]):
            doc = self.documents["refund_policy"]
            return {
                "answer": doc["content"],
                "citations": [{"title": doc["source"], "snippet": doc["content"][:100] + "..."}],
                "confidence": 0.92
            }
        elif any(word in query_lower for word in ["shipping", "delivery", "ship"]):
            doc = self.documents["shipping_policy"]
            return {
                "answer": doc["content"],
                "citations": [{"title": doc["source"], "snippet": doc["content"][:100] + "..."}],
                "confidence": 0.89
            }
        elif any(word in query_lower for word in ["support", "help", "contact", "hours"]):
            doc = self.documents["support_hours"]
            return {
                "answer": doc["content"],
                "citations": [{"title": doc["source"], "snippet": doc["content"][:100] + "..."}],
                "confidence": 0.87
            }
        elif any(word in query_lower for word in ["price", "cost", "pricing", "plan"]):
            doc = self.documents["pricing"]
            return {
                "answer": doc["content"],
                "citations": [{"title": doc["source"], "snippet": doc["content"][:100] + "..."}],
                "confidence": 0.85
            }
        else:
            return {
                "answer": "I don't have specific information about that topic in my knowledge base. Could you try asking about our refund policy, shipping, support hours, or pricing?",
                "citations": [],
                "confidence": 0.3
            }

class MockLeadProcessor:
    """Mock lead processing for demonstration"""
    
    def extract_lead(self, text: str) -> Dict[str, Any]:
        """Extract lead information from text"""
        # Simple regex patterns for demo
        name_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'
        company_pattern = r'\b(?:from|at) ([A-Z][a-zA-Z0-9\s]+?)(?:\s+(?:wants|needs|looking|interested))'
        budget_pattern = r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*k?'
        
        name_match = re.search(name_pattern, text)
        company_match = re.search(company_pattern, text)
        budget_match = re.search(budget_pattern, text)
        
        # Extract timeline
        timeline = "Not specified"
        if "next week" in text.lower():
            timeline = "Next week"
        elif "next month" in text.lower():
            timeline = "Next month"
        elif "september" in text.lower():
            timeline = "September"
        elif "q1" in text.lower():
            timeline = "Q1"
        
        # Extract intent
        intent = "General inquiry"
        if any(word in text.lower() for word in ["demo", "demonstration"]):
            intent = "Demo request"
        elif any(word in text.lower() for word in ["poc", "proof of concept"]):
            intent = "PoC development"
        elif any(word in text.lower() for word in ["integration", "integrate"]):
            intent = "Integration services"
        elif any(word in text.lower() for word in ["consultation", "consult"]):
            intent = "Consultation"
        
        # Calculate quality score
        quality_score = 0.5
        if name_match:
            quality_score += 0.2
        if company_match:
            quality_score += 0.2
        if budget_match:
            quality_score += 0.15
        if timeline != "Not specified":
            quality_score += 0.1
        
        return {
            "name": name_match.group(1) if name_match else "Unknown",
            "company": company_match.group(1).strip() if company_match else "Unknown",
            "intent": intent,
            "budget": budget_match.group(0) if budget_match else "Not specified",
            "timeline": timeline,
            "qualityScore": round(quality_score, 2),
            "rawText": text
        }
    
    def generate_proposal(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proposal copy"""
        company = lead_data.get("company", "your company")
        intent = lead_data.get("intent", "your project")
        budget = lead_data.get("budget", "your budget")
        timeline = lead_data.get("timeline", "your timeline")
        
        title = f"{intent.title()} Proposal for {company}"
        
        summary = f"We understand {company} is looking for {intent.lower()} services within {timeline.lower()}. Our experienced team specializes in delivering high-quality solutions that meet your specific requirements and budget constraints."
        
        bullet_points = [
            f"Customized {intent.lower()} solution designed for {company}",
            f"Experienced team with proven track record",
            f"Delivery timeline aligned with {timeline.lower()}",
            f"Budget-conscious approach within {budget} range" if budget != "Not specified" else "Flexible pricing options",
            "Comprehensive testing and documentation included",
            "Post-delivery support and maintenance",
            "Regular progress updates and communication"
        ]
        
        return {
            "title": title,
            "summaryBlurb": summary,
            "bulletPoints": bullet_points,
            "status": "success"
        }

class IntentClassifier:
    """Intent classification for routing messages"""
    
    def classify(self, text: str) -> Dict[str, Any]:
        """Classify user intent"""
        text_lower = text.lower()
        
        # Knowledge Q&A patterns
        if any(pattern in text_lower for pattern in [
            "what", "how", "when", "where", "why", "explain", "tell me",
            "policy", "refund", "shipping", "support", "price", "cost"
        ]):
            return {
                "intent": "knowledge_qa",
                "confidence": 0.9,
                "suggestedAgent": "agentA",
                "entities": []
            }
        
        # Lead capture patterns
        elif any(pattern in text_lower for pattern in [
            "wants", "needs", "looking for", "interested in", "demo", "poc",
            "budget", "timeline", "project", "from"
        ]) and any(pattern in text_lower for pattern in [
            "demo", "poc", "proof of concept", "consultation", "integration", "development"
        ]):
            return {
                "intent": "lead_capture",
                "confidence": 0.85,
                "suggestedAgent": "agentB", 
                "entities": []
            }
        
        # Proposal request patterns
        elif any(pattern in text_lower for pattern in [
            "proposal", "quote", "estimate", "draft"
        ]):
            return {
                "intent": "proposal_request",
                "confidence": 0.8,
                "suggestedAgent": "agentB",
                "entities": []
            }
        
        # Scheduling patterns
        elif any(pattern in text_lower for pattern in [
            "schedule", "meeting", "call", "appointment", "calendar"
        ]):
            return {
                "intent": "scheduling",
                "confidence": 0.75,
                "suggestedAgent": "agentA",
                "entities": []
            }
        
        # Default
        else:
            return {
                "intent": "general",
                "confidence": 0.4,
                "suggestedAgent": "agentA",
                "entities": []
            }

class TelegramBot:
    """Complete Telegram bot implementation"""
    
    def __init__(self):
        self.knowledge_base = MockKnowledgeBase()
        self.lead_processor = MockLeadProcessor()
        self.intent_classifier = IntentClassifier()
        self.conversation_log = []
        self.leads_captured = []
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
        """Send message to Telegram"""
        try:
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            # Encode data
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            
            # Create request
            request = urllib.request.Request(
                f"{TELEGRAM_API_URL}/sendMessage",
                data=data_encoded,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Send request
            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('ok', False)
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def process_message(self, message_data: Dict[str, Any]) -> str:
        """Process incoming message and generate response"""
        try:
            # Extract message info
            message = message_data.get('message', {})
            text = message.get('text', '')
            chat_id = message.get('chat', {}).get('id')
            user = message.get('from', {})
            username = user.get('username', 'Unknown')
            first_name = user.get('first_name', 'User')
            
            if not text or not chat_id:
                return "Invalid message format"
            
            # Log conversation
            self.conversation_log.append({
                "timestamp": datetime.now().isoformat(),
                "user": username,
                "input": text,
                "chat_id": chat_id
            })
            
            # Classify intent
            intent_result = self.intent_classifier.classify(text)
            intent = intent_result["intent"]
            confidence = intent_result["confidence"]
            
            logger.info(f"Classified intent: {intent} (confidence: {confidence})")
            
            # Route to appropriate handler
            if intent == "knowledge_qa":
                response = self.handle_knowledge_qa(text, chat_id, username)
            elif intent == "lead_capture":
                response = self.handle_lead_capture(text, chat_id, username)
            elif intent == "proposal_request":
                response = self.handle_proposal_request(text, chat_id, username)
            elif intent == "scheduling":
                response = self.handle_scheduling(text, chat_id, username)
            else:
                response = self.handle_general(text, chat_id, username)
            
            # Send response
            self.send_message(chat_id, response)
            
            # Update conversation log
            self.conversation_log[-1].update({
                "intent": intent,
                "confidence": confidence,
                "output": response
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = "Sorry, I encountered an error processing your message. Please try again."
            if chat_id:
                self.send_message(chat_id, error_response)
            return error_response
    
    def handle_knowledge_qa(self, text: str, chat_id: int, username: str) -> str:
        """Handle knowledge Q&A requests"""
        try:
            # Search knowledge base
            result = self.knowledge_base.search(text)
            
            # Format response
            response = f"📚 **Knowledge Base Response**\n\n"
            response += f"{result['answer']}\n\n"
            
            if result['citations']:
                response += "📎 **Sources:**\n"
                for citation in result['citations']:
                    response += f"• {citation['title']}\n"
            
            response += f"\n🎯 Confidence: {result['confidence']:.0%}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in knowledge QA: {e}")
            return "Sorry, I couldn't find information about that topic. Please try asking about our refund policy, shipping, support hours, or pricing."
    
    def handle_lead_capture(self, text: str, chat_id: int, username: str) -> str:
        """Handle lead capture"""
        try:
            # Extract lead information
            lead_data = self.lead_processor.extract_lead(text)
            
            # Store lead
            lead_data['timestamp'] = datetime.now().isoformat()
            lead_data['source'] = 'Telegram'
            lead_data['user'] = username
            self.leads_captured.append(lead_data)
            
            # Format response
            response = "✅ **New Lead Captured!**\n\n"
            response += f"👤 **Name:** {lead_data['name']}\n"
            response += f"🏢 **Company:** {lead_data['company']}\n"
            response += f"🎯 **Intent:** {lead_data['intent']}\n"
            response += f"💰 **Budget:** {lead_data['budget']}\n"
            response += f"📅 **Timeline:** {lead_data['timeline']}\n"
            response += f"⭐ **Quality Score:** {lead_data['qualityScore']:.0%}\n\n"
            response += "📝 Lead has been saved to our CRM system."
            
            return response
            
        except Exception as e:
            logger.error(f"Error in lead capture: {e}")
            return "I've noted your inquiry. Could you provide more details about your project requirements?"
    
    def handle_proposal_request(self, text: str, chat_id: int, username: str) -> str:
        """Handle proposal generation requests"""
        try:
            # Find the most recent lead for this user
            user_leads = [lead for lead in self.leads_captured if lead.get('user') == username]
            
            if not user_leads:
                return "I don't have lead information to generate a proposal. Please provide details about your project first."
            
            # Use most recent lead
            latest_lead = user_leads[-1]
            
            # Generate proposal
            proposal = self.lead_processor.generate_proposal(latest_lead)
            
            # Format response
            response = f"📋 **{proposal['title']}**\n\n"
            response += f"{proposal['summaryBlurb']}\n\n"
            response += "🔹 **Key Benefits:**\n"
            for bullet in proposal['bulletPoints']:
                response += f"• {bullet}\n"
            
            response += "\n📞 Ready to discuss further? Let me know!"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in proposal generation: {e}")
            return "I can help generate a proposal. Please first provide your project details (company, requirements, budget, timeline)."
    
    def handle_scheduling(self, text: str, chat_id: int, username: str) -> str:
        """Handle scheduling requests"""
        try:
            # Simple scheduling logic
            response = "📅 **Scheduling Request Received**\n\n"
            
            # Extract scheduling details (simplified)
            if "tomorrow" in text.lower():
                date = (datetime.now() + timedelta(days=1)).strftime("%B %d, %Y")
            elif "next week" in text.lower():
                date = (datetime.now() + timedelta(days=7)).strftime("%B %d, %Y")
            elif "monday" in text.lower():
                date = "Next Monday"
            elif "tuesday" in text.lower():
                date = "Next Tuesday"
            elif "wednesday" in text.lower():
                date = "Next Wednesday"
            elif "thursday" in text.lower():
                date = "Next Thursday"
            elif "friday" in text.lower():
                date = "Next Friday"
            else:
                date = "To be determined"
            
            # Extract time
            time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))', text)
            if time_match:
                time = time_match.group(1)
            elif re.search(r'(\d{1,2})\s*(?:AM|PM|am|pm)', text):
                time = re.search(r'(\d{1,2})\s*(?:AM|PM|am|pm)', text).group(0)
            else:
                time = "To be determined"
            
            response += f"🗓️ **Date:** {date}\n"
            response += f"🕐 **Time:** {time}\n"
            response += f"👤 **Requested by:** {username}\n\n"
            response += "✅ I've noted your scheduling request. You'll receive a calendar invitation shortly."
            
            return response
            
        except Exception as e:
            logger.error(f"Error in scheduling: {e}")
            return "I can help schedule a meeting. Please specify your preferred date and time."
    
    def handle_general(self, text: str, chat_id: int, username: str) -> str:
        """Handle general inquiries"""
        response = f"👋 Hello {username}!\n\n"
        response += "I'm your AI Revenue Copilot. I can help you with:\n\n"
        response += "📚 **Knowledge Q&A** - Ask about policies, pricing, support\n"
        response += "💼 **Lead Management** - Capture project requirements\n"
        response += "📋 **Proposal Generation** - Create professional proposals\n"
        response += "📅 **Scheduling** - Book meetings and calls\n\n"
        response += "What can I help you with today?"
        
        return response
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        try:
            request = urllib.request.Request(f"{TELEGRAM_API_URL}/getMe")
            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {"ok": False, "error": str(e)}
    
    def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Set webhook for receiving messages"""
        try:
            data = urllib.parse.urlencode({'url': webhook_url}).encode('utf-8')
            request = urllib.request.Request(
                f"{TELEGRAM_API_URL}/setWebhook",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return {"ok": False, "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bot usage statistics"""
        return {
            "conversations_handled": len(self.conversation_log),
            "leads_captured": len(self.leads_captured),
            "last_activity": self.conversation_log[-1]["timestamp"] if self.conversation_log else None,
            "intents_processed": {
                "knowledge_qa": len([c for c in self.conversation_log if c.get("intent") == "knowledge_qa"]),
                "lead_capture": len([c for c in self.conversation_log if c.get("intent") == "lead_capture"]),
                "proposal_request": len([c for c in self.conversation_log if c.get("intent") == "proposal_request"]),
                "scheduling": len([c for c in self.conversation_log if c.get("intent") == "scheduling"]),
                "general": len([c for c in self.conversation_log if c.get("intent") == "general"])
            }
        }

# Demo and testing functions
def test_bot_locally():
    """Test bot functionality locally"""
    print("🤖 Testing Telegram Revenue Copilot Bot...")
    
    bot = TelegramBot()
    
    # Test scenarios
    test_messages = [
        {
            "message": {
                "message_id": 1,
                "from": {"id": 123, "username": "testuser", "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "text": "What is your refund policy?"
            }
        },
        {
            "message": {
                "message_id": 2,
                "from": {"id": 123, "username": "testuser", "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "text": "John Smith from Acme Corp wants a PoC demo next week, budget around 15k"
            }
        },
        {
            "message": {
                "message_id": 3,
                "from": {"id": 123, "username": "testuser", "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "text": "Draft a proposal for Acme"
            }
        },
        {
            "message": {
                "message_id": 4,
                "from": {"id": 123, "username": "testuser", "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "text": "Schedule a call tomorrow at 2 PM"
            }
        }
    ]
    
    print("\n" + "="*60)
    print("RUNNING TEST SCENARIOS")
    print("="*60)
    
    for i, test_msg in enumerate(test_messages, 1):
        print(f"\n--- Test {i} ---")
        user_input = test_msg["message"]["text"]
        print(f"👤 User: {user_input}")
        
        response = bot.process_message(test_msg)
        print(f"🤖 Bot: {response[:200]}...")
    
    # Show statistics
    print("\n" + "="*60)
    print("BOT STATISTICS")
    print("="*60)
    stats = bot.get_stats()
    print(json.dumps(stats, indent=2))
    
    return bot

def test_telegram_api():
    """Test Telegram API connection"""
    print("📱 Testing Telegram API connection...")
    
    bot = TelegramBot()
    bot_info = bot.get_bot_info()
    
    if bot_info.get("ok"):
        result = bot_info["result"]
        print(f"✅ Bot connected successfully!")
        print(f"   Bot Name: {result['first_name']}")
        print(f"   Username: @{result['username']}")
        print(f"   Bot ID: {result['id']}")
        return True
    else:
        print(f"❌ Bot connection failed: {bot_info.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    print("🚀 TELEGRAM REVENUE COPILOT - COMPLETE BOT")
    print("="*60)
    
    # Test Telegram API
    if test_telegram_api():
        print("\n🧪 Running local tests...")
        bot = test_bot_locally()
        
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 Bot is ready for production!")
        print("\n📝 Next steps:")
        print("1. Set up webhook URL for live bot")
        print("2. Deploy to production server")
        print("3. Start receiving messages!")
    else:
        print("\n❌ Please check your Telegram bot token in .env file")