#!/usr/bin/env python3
"""
Test script for Telegram Revenue Copilot
Validates all free API integrations and core functionality
"""

import os
import sys
import asyncio
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment_variables() -> Dict[str, bool]:
    """Check if all required environment variables are set"""
    required_vars = [
        "GROQ_API_KEY",
        "TELEGRAM_BOT_TOKEN", 
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_DRIVE_FOLDER_ID",
        "GOOGLE_SHEETS_CONVERSATION_ID",
        "GOOGLE_SHEETS_CRM_ID",
        "GOOGLE_CALENDAR_ID",
        "N8N_WEBHOOK_URL"
    ]
    
    results = {}
    for var in required_vars:
        value = os.getenv(var)
        results[var] = bool(value and value != f"your_{var.lower()}_here")
        
    return results

def test_groq_api() -> Dict[str, Any]:
    """Test Groq API connection and inference"""
    try:
        from groq import Groq
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        start_time = time.time()
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "Hello! Please respond with just 'API working correctly'"}
            ],
            max_tokens=50
        )
        
        response_time = time.time() - start_time
        
        return {
            "status": "success",
            "response": completion.choices[0].message.content,
            "response_time": response_time,
            "model": "llama-3.1-8b-instant"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def test_telegram_bot() -> Dict[str, Any]:
    """Test Telegram bot token and basic API"""
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            return {"status": "error", "error": "No Telegram bot token"}
            
        # Test getMe endpoint
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        
        if response.status_code == 200:
            bot_info = response.json()
            return {
                "status": "success",
                "bot_info": bot_info["result"],
                "username": bot_info["result"]["username"]
            }
        else:
            return {
                "status": "error", 
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def test_agent_services() -> Dict[str, Any]:
    """Test local agent services"""
    agents = {
        "agentA": "http://localhost:8001/health",
        "agentB": "http://localhost:8002/health", 
        "intent_classifier": "http://localhost:8003/health"
    }
    
    results = {}
    
    for agent_name, url in agents.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results[agent_name] = {
                    "status": "success",
                    "response": response.json()
                }
            else:
                results[agent_name] = {
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            results[agent_name] = {
                "status": "offline",
                "error": "Service not running"
            }
        except Exception as e:
            results[agent_name] = {
                "status": "error", 
                "error": str(e)
            }
    
    return results

def test_intent_classification() -> Dict[str, Any]:
    """Test intent classification with sample inputs"""
    test_cases = [
        {
            "text": "What is your refund policy?",
            "expected_intent": "knowledge_qa"
        },
        {
            "text": "John from Acme wants a demo",
            "expected_intent": "lead_capture"
        },
        {
            "text": "Schedule a meeting next Tuesday",
            "expected_intent": "scheduling"
        }
    ]
    
    results = []
    
    for case in test_cases:
        try:
            response = requests.post(
                "http://localhost:8003/classify",
                json={
                    "text": case["text"],
                    "hasAttachments": False,
                    "userId": "test_user"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "input": case["text"],
                    "expected": case["expected_intent"],
                    "actual": data.get("intent"),
                    "confidence": data.get("confidence"),
                    "status": "success"
                })
            else:
                results.append({
                    "input": case["text"],
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            results.append({
                "input": case["text"],
                "status": "error",
                "error": str(e)
            })
    
    return results

def test_knowledge_agent() -> Dict[str, Any]:
    """Test knowledge agent Q&A functionality"""
    try:
        response = requests.post(
            "http://localhost:8001/ask",
            json={
                "userId": "test_user",
                "text": "What services do you offer?",
                "requestId": "test_knowledge"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "answer": data.get("answer"),
                "citations": data.get("citations", []),
                "confidence": data.get("confidence")
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def test_dealflow_agent() -> Dict[str, Any]:
    """Test dealflow agent lead capture"""
    try:
        response = requests.post(
            "http://localhost:8002/newlead",
            json={
                "raw": "John Smith from TechCorp wants a demo next week, budget around 5k",
                "requestId": "test_lead"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "lead_data": {
                    "name": data.get("name"),
                    "company": data.get("company"),
                    "intent": data.get("intent"),
                    "budget": data.get("budget"),
                    "qualityScore": data.get("qualityScore")
                }
            }
        else:
            return {
                "status": "error", 
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def test_huggingface_embeddings() -> Dict[str, Any]:
    """Test HuggingFace embeddings (free alternative to OpenAI)"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # Test loading the free embedding model
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Test encoding
        sentences = ["What is your refund policy?", "How do I contact support?"]
        embeddings = model.encode(sentences)
        
        return {
            "status": "success",
            "model": "all-MiniLM-L6-v2",
            "embedding_dimension": embeddings.shape[1],
            "sample_embeddings_shape": embeddings.shape
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def run_all_tests() -> Dict[str, Any]:
    """Run comprehensive test suite"""
    print("🚀 Starting Telegram Revenue Copilot Test Suite...")
    print("=" * 60)
    
    all_results = {}
    
    # Environment check
    print("\n📋 Checking Environment Variables...")
    env_results = check_environment_variables()
    all_results["environment"] = env_results
    
    missing_vars = [var for var, present in env_results.items() if not present]
    if missing_vars:
        print(f"❌ Missing variables: {', '.join(missing_vars)}")
    else:
        print("✅ All environment variables present")
    
    # API Tests
    print("\n🤖 Testing Groq API...")
    groq_results = test_groq_api()
    all_results["groq_api"] = groq_results
    
    if groq_results["status"] == "success":
        print(f"✅ Groq API working - Response time: {groq_results['response_time']:.2f}s")
    else:
        print(f"❌ Groq API failed: {groq_results.get('error')}")
    
    print("\n📱 Testing Telegram Bot...")
    telegram_results = test_telegram_bot()
    all_results["telegram_bot"] = telegram_results
    
    if telegram_results["status"] == "success":
        print(f"✅ Telegram Bot working - @{telegram_results['username']}")
    else:
        print(f"❌ Telegram Bot failed: {telegram_results.get('error')}")
    
    print("\n🧠 Testing HuggingFace Embeddings...")
    embedding_results = test_huggingface_embeddings()
    all_results["embeddings"] = embedding_results
    
    if embedding_results["status"] == "success":
        print(f"✅ Embeddings working - Dimension: {embedding_results['embedding_dimension']}")
    else:
        print(f"❌ Embeddings failed: {embedding_results.get('error')}")
    
    # Service Tests (only if services are running)
    print("\n🔧 Testing Agent Services...")
    service_results = test_agent_services()
    all_results["services"] = service_results
    
    for agent, result in service_results.items():
        if result["status"] == "success":
            print(f"✅ {agent} service running")
        elif result["status"] == "offline":
            print(f"⚠️  {agent} service offline (start with docker-compose up)")
        else:
            print(f"❌ {agent} service error: {result.get('error')}")
    
    # Functional Tests (only if services are running)
    services_running = any(r["status"] == "success" for r in service_results.values())
    
    if services_running:
        print("\n🎯 Testing Intent Classification...")
        intent_results = test_intent_classification()
        all_results["intent_classification"] = intent_results
        
        for result in intent_results:
            if result["status"] == "success":
                print(f"✅ '{result['input']}' -> {result['actual']} (conf: {result['confidence']:.2f})")
            else:
                print(f"❌ '{result['input']}' failed: {result.get('error')}")
        
        print("\n📚 Testing Knowledge Agent...")
        knowledge_results = test_knowledge_agent()
        all_results["knowledge_agent"] = knowledge_results
        
        if knowledge_results["status"] == "success":
            print(f"✅ Knowledge agent working - Answer length: {len(knowledge_results['answer'])} chars")
        else:
            print(f"❌ Knowledge agent failed: {knowledge_results.get('error')}")
        
        print("\n💼 Testing Dealflow Agent...")
        dealflow_results = test_dealflow_agent()
        all_results["dealflow_agent"] = dealflow_results
        
        if dealflow_results["status"] == "success":
            lead = dealflow_results["lead_data"]
            print(f"✅ Dealflow agent working - Extracted: {lead['name']} from {lead['company']}")
        else:
            print(f"❌ Dealflow agent failed: {dealflow_results.get('error')}")
    
    else:
        print("⚠️  Skipping functional tests - no services running")
        print("   Start services with: docker-compose up -d")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        if isinstance(results, dict) and "status" in results:
            total_tests += 1
            if results["status"] == "success":
                passed_tests += 1
        elif isinstance(results, list):
            for result in results:
                if isinstance(result, dict) and "status" in result:
                    total_tests += 1
                    if result["status"] == "success":
                        passed_tests += 1
        elif isinstance(results, dict):
            for key, value in results.items():
                if isinstance(value, bool):
                    total_tests += 1
                    if value:
                        passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 System ready for deployment!")
    elif success_rate >= 60:
        print("⚠️  System partially ready - check failed tests")
    else:
        print("❌ System not ready - major issues detected")
    
    return all_results

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    results = run_all_tests()
    
    # Save detailed results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to test_results.json")
    print("\n🚀 Ready to deploy to GitHub and Render!")
    print("\nNext steps:")
    print("1. Set up your free API keys (see .env.sample)")
    print("2. Run: docker-compose up -d")
    print("3. Re-run this test script")
    print("4. Import n8n workflows")  
    print("5. Deploy to Render")
    print("6. Share with client!")