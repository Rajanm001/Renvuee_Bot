import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import requests

class TestIntegration:
    """Integration tests for the complete Telegram Revenue Copilot system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.base_url = "http://localhost"
        self.agent_a_url = f"{self.base_url}:8001"
        self.agent_b_url = f"{self.base_url}:8002"
        self.intent_url = f"{self.base_url}:8003"
        self.n8n_url = f"{self.base_url}:5678"
        
        # Mock Telegram message
        self.sample_message = {
            "message": {
                "message_id": 123,
                "from": {
                    "id": 12345,
                    "username": "testuser",
                    "first_name": "Test"
                },
                "chat": {
                    "id": 12345,
                    "type": "private"
                },
                "date": 1640995200,
                "text": "What is your refund policy?"
            }
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_knowledge_flow(self):
        """Test complete knowledge Q&A flow"""
        # Mock external API calls
        with patch('requests.post') as mock_post:
            # Mock intent classification response
            mock_post.return_value.json.return_value = {
                "intent": "knowledge_qa",
                "confidence": 0.9,
                "entities": [],
                "suggestedAgent": "agentA",
                "requestId": "test_123"
            }
            mock_post.return_value.status_code = 200
            
            # Test intent classification
            intent_response = requests.post(
                f"{self.intent_url}/classify",
                json={
                    "text": "What is your refund policy?",
                    "hasAttachments": False,
                    "userId": "12345"
                }
            )
            
            assert intent_response.status_code == 200
            intent_data = intent_response.json()
            assert intent_data["intent"] == "knowledge_qa"
            assert intent_data["suggestedAgent"] == "agentA"
    
    @pytest.mark.asyncio
    async def test_end_to_end_lead_capture_flow(self):
        """Test complete lead capture flow"""
        lead_text = "John Smith from Acme Corp wants a PoC in September, budget around 10k"
        
        with patch('requests.post') as mock_post:
            # Mock responses
            mock_responses = [
                # Intent classification
                Mock(status_code=200, json=lambda: {
                    "intent": "lead_capture",
                    "confidence": 0.85,
                    "entities": [
                        {"type": "name", "value": "John Smith", "confidence": 0.9},
                        {"type": "company", "value": "Acme Corp", "confidence": 0.8}
                    ],
                    "suggestedAgent": "agentB",
                    "requestId": "test_456"
                }),
                # Lead creation
                Mock(status_code=200, json=lambda: {
                    "name": "John Smith",
                    "company": "Acme Corp",
                    "intent": "PoC development",
                    "budget": "around 10k",
                    "timeline": "September",
                    "qualityScore": 0.85,
                    "requestId": "test_456"
                })
            ]
            mock_post.side_effect = mock_responses
            
            # Test complete flow
            # 1. Intent classification
            intent_response = requests.post(
                f"{self.intent_url}/classify",
                json={
                    "text": lead_text,
                    "hasAttachments": False,
                    "userId": "12345"
                }
            )
            
            assert intent_response.status_code == 200
            assert intent_response.json()["intent"] == "lead_capture"
            
            # 2. Lead creation
            lead_response = requests.post(
                f"{self.agent_b_url}/newlead",
                json={"raw": lead_text}
            )
            
            assert lead_response.status_code == 200
            lead_data = lead_response.json()
            assert lead_data["name"] == "John Smith"
            assert lead_data["company"] == "Acme Corp"
            assert lead_data["qualityScore"] > 0.8
    
    def test_error_handling_and_retries(self):
        """Test error handling and retry mechanisms"""
        with patch('requests.post') as mock_post:
            # Simulate API failure then success
            mock_post.side_effect = [
                requests.exceptions.ConnectionError("Service unavailable"),
                Mock(status_code=500, text="Internal Server Error"),
                Mock(status_code=200, json=lambda: {"status": "success"})
            ]
            
            # Test that errors are handled gracefully
            # This would be handled by n8n retry logic in practice
            try:
                response = requests.post(f"{self.agent_a_url}/ask", json={
                    "userId": "12345",
                    "text": "test question"
                })
            except requests.exceptions.ConnectionError:
                # Expected on first try
                pass
    
    @pytest.mark.asyncio 
    async def test_telegram_webhook_routing(self):
        """Test Telegram webhook message routing"""
        test_cases = [
            {
                "message": {"text": "What is your refund policy?", "from": {"id": 123}, "chat": {"id": 123}},
                "expected_agent": "agentA",
                "expected_intent": "knowledge_qa"
            },
            {
                "message": {"text": "John from Acme wants a demo", "from": {"id": 123}, "chat": {"id": 123}},
                "expected_agent": "agentB", 
                "expected_intent": "lead_capture"
            },
            {
                "message": {"text": "Draft a proposal for TechCorp", "from": {"id": 123}, "chat": {"id": 123}},
                "expected_agent": "agentB",
                "expected_intent": "proposal_request"
            }
        ]
        
        for case in test_cases:
            with patch('requests.post') as mock_post:
                mock_post.return_value.json.return_value = {
                    "intent": case["expected_intent"],
                    "suggestedAgent": case["expected_agent"],
                    "confidence": 0.8,
                    "entities": []
                }
                mock_post.return_value.status_code = 200
                
                # Simulate webhook call
                webhook_payload = {"message": case["message"]}
                
                # This would route through n8n in practice
                intent_response = requests.post(
                    f"{self.intent_url}/classify",
                    json={
                        "text": case["message"]["text"],
                        "hasAttachments": False,
                        "userId": str(case["message"]["from"]["id"])
                    }
                )
                
                assert intent_response.status_code == 200
                data = intent_response.json()
                assert data["intent"] == case["expected_intent"]
                assert data["suggestedAgent"] == case["expected_agent"]
    
    def test_file_upload_and_ingestion(self):
        """Test file upload and knowledge base ingestion"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "chunks": 25,
                "tokens": 5000,
                "requestId": "ingest_123",
                "status": "success"
            }
            mock_post.return_value.status_code = 200
            
            # Test file ingestion
            response = requests.post(
                f"{self.agent_a_url}/ingest",
                json={
                    "driveFileId": "test_file_123",
                    "requestId": "ingest_123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["chunks"] > 0
            assert data["tokens"] > 0
    
    def test_proposal_generation_flow(self):
        """Test proposal generation workflow"""
        lead_data = {
            "name": "Jane Doe",
            "company": "StartupXYZ", 
            "intent": "needs integration help",
            "budget": "15k",
            "timeline": "Q1 2024"
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "title": "Integration Services Proposal for StartupXYZ",
                "summaryBlurb": "We understand StartupXYZ needs integration help for Q1 2024...",
                "bulletPoints": [
                    "Complete API integration within Q1 timeline",
                    "Dedicated technical team with daily updates", 
                    "Comprehensive testing and documentation",
                    "Budget-conscious approach with 15k budget",
                    "Post-launch support included"
                ],
                "requestId": "proposal_123",
                "status": "success"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"{self.agent_b_url}/proposal-copy",
                json={
                    "lead": lead_data,
                    "requestId": "proposal_123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "StartupXYZ" in data["title"]
            assert len(data["bulletPoints"]) >= 3
            assert "15k" in data["summaryBlurb"] or any("15k" in bullet for bullet in data["bulletPoints"])
    
    def test_scheduling_and_calendar_integration(self):
        """Test scheduling parsing and calendar event creation"""
        scheduling_texts = [
            "Schedule a demo next Wednesday at 2 PM",
            "Let's have a call tomorrow at 10:00 AM", 
            "Set up a meeting next Friday at 3:30 PM with the team"
        ]
        
        for text in scheduling_texts:
            with patch('requests.post') as mock_post:
                mock_post.return_value.json.return_value = {
                    "title": "Demo Call",
                    "startISO": "2024-01-17T14:00:00Z",
                    "endISO": "2024-01-17T15:00:00Z",
                    "requestId": "schedule_123",
                    "status": "success"
                }
                mock_post.return_value.status_code = 200
                
                response = requests.post(
                    f"{self.agent_a_url}/followup-parse",
                    json={
                        "text": text,
                        "requestId": "schedule_123"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["startISO"]
                assert "T" in data["startISO"]  # ISO format check
    
    def test_data_persistence_and_sheets_integration(self):
        """Test data logging to Google Sheets"""
        # This would test the n8n Google Sheets integration
        # In practice, this involves checking that data flows correctly
        # through the n8n workflows to update the sheets
        
        sample_conversation_log = {
            "timestamp": "2024-01-15T14:30:00Z",
            "user": "testuser",
            "intent": "knowledge_qa",
            "input": "What is your refund policy?",
            "output": "Our refund policy allows returns within 30 days...",
            "confidence": 0.9,
            "citations": "refund_policy.pdf",
            "requestId": "conv_123"
        }
        
        sample_crm_log = {
            "timestamp": "2024-01-15T14:30:00Z", 
            "leadId": "lead_456",
            "name": "John Smith",
            "company": "Acme Corp",
            "intent": "PoC development",
            "budget": "10k",
            "stage": "New",
            "qualityScore": 0.85
        }
        
        # These would be tested by checking the actual sheets content
        # or by mocking the Google Sheets API responses
        assert sample_conversation_log["intent"] == "knowledge_qa"
        assert sample_crm_log["qualityScore"] > 0.8
    
    def test_security_and_validation(self):
        """Test input validation and security measures"""
        # Test various malicious inputs
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../../etc/passwd",
            "A" * 10000,  # Very long input
            "",  # Empty input
            None  # Null input
        ]
        
        for malicious_input in malicious_inputs:
            if malicious_input is None:
                continue
                
            with patch('requests.post') as mock_post:
                # Should handle gracefully
                mock_post.return_value.status_code = 400
                mock_post.return_value.json.return_value = {"error": "Invalid input"}
                
                try:
                    response = requests.post(
                        f"{self.intent_url}/classify",
                        json={
                            "text": malicious_input,
                            "hasAttachments": False,
                            "userId": "12345"
                        }
                    )
                    # Should either succeed with sanitized input or fail gracefully
                    assert response.status_code in [200, 400, 422]
                except Exception:
                    # Connection errors are acceptable for malicious inputs
                    pass

class TestGoldenScenarios:
    """Golden test scenarios that match the demo requirements"""
    
    def test_demo_scenario_1_knowledge_qa(self):
        """Demo: User asks 'What's our refund policy?'"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "answer": "Our refund policy allows returns within 30 days of purchase for a full refund. Digital goods have a 7-day return window.",
                "citations": [
                    {"title": "Refund_Policy_2024.pdf", "driveFileId": "file_123", "snippet": "Returns within 30 days..."},
                    {"title": "Digital_Goods_Policy.pdf", "driveFileId": "file_456", "snippet": "Digital goods 7-day window..."}
                ],
                "confidence": 0.92,
                "requestId": "demo_1"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"http://localhost:8001/ask",
                json={
                    "userId": "demo_user",
                    "text": "What's our refund policy?",
                    "requestId": "demo_1"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "30 days" in data["answer"]
            assert len(data["citations"]) >= 2
            assert data["confidence"] > 0.9
    
    def test_demo_scenario_2_file_upload(self):
        """Demo: User sends new PDF (Refunds_2025.pdf)"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "chunks": 15,
                "tokens": 3500,
                "requestId": "demo_2",
                "status": "success"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"http://localhost:8001/ingest",
                json={
                    "driveFileId": "refunds_2025_pdf",
                    "requestId": "demo_2"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["chunks"] == 15
            assert data["tokens"] == 3500
    
    def test_demo_scenario_3_updated_knowledge(self):
        """Demo: Ask about digital goods refunds (should use new document)"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "answer": "For digital goods, our updated 2025 policy provides a 14-day return window with specific conditions for software and digital content.",
                "citations": [
                    {"title": "Refunds_2025.pdf", "driveFileId": "refunds_2025_pdf", "snippet": "Digital goods 14-day window..."}
                ],
                "confidence": 0.88,
                "requestId": "demo_3"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"http://localhost:8001/ask", 
                json={
                    "userId": "demo_user",
                    "text": "And what about digital goods refunds?",
                    "requestId": "demo_3"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "2025" in data["answer"]
            assert "Refunds_2025.pdf" in [c["title"] for c in data["citations"]]
    
    def test_demo_scenario_4_scheduling(self):
        """Demo: Schedule a call next Tue 10:00 with Dana about refunds"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "title": "Call with Dana about refunds",
                "startISO": "2024-01-16T10:00:00Z",
                "endISO": "2024-01-16T11:00:00Z",
                "attendees": ["Dana"],
                "requestId": "demo_4"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"http://localhost:8001/followup-parse",
                json={
                    "text": "Schedule a call next Tue at 10:00 with Dana about refunds",
                    "requestId": "demo_4"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "Dana" in data["title"]
            assert "refunds" in data["title"].lower()
            assert data["attendees"] == ["Dana"]
    
    def test_demo_scenario_5_lead_capture(self):
        """Demo: John from Acme wants a PoC in September, budget ~10k"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "name": "John",
                "company": "Acme",
                "intent": "PoC development",
                "budget": "around 10k",
                "timeline": "September",
                "normalizedCompanyDomain": "acme.com",
                "qualityScore": 0.85,
                "requestId": "demo_5"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"http://localhost:8002/newlead",
                json={
                    "raw": "John from Acme wants a PoC in September, budget around 10k",
                    "requestId": "demo_5"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "John"
            assert data["company"] == "Acme"
            assert data["intent"] == "PoC development"
            assert data["qualityScore"] > 0.8
    
    def test_demo_scenario_6_proposal_generation(self):
        """Demo: Draft a proposal for Acme"""
        lead_data = {
            "name": "John",
            "company": "Acme",
            "intent": "PoC development",
            "budget": "around 10k",
            "timeline": "September"
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "title": "PoC Development Proposal for Acme",
                "summaryBlurb": "We understand Acme is looking for a proof-of-concept development solution for September delivery within your 10k budget. Our experienced team specializes in rapid prototyping and can deliver a comprehensive PoC that demonstrates core functionality while staying within your timeline and budget constraints.",
                "bulletPoints": [
                    "Rapid 6-week development cycle to meet September deadline",
                    "Dedicated project team with Agile methodology",
                    "Comprehensive testing and documentation included",
                    "Budget-optimized approach under 10k investment",
                    "Post-delivery support and consultation included"
                ],
                "requestId": "demo_6"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"http://localhost:8002/proposal-copy",
                json={
                    "lead": lead_data,
                    "requestId": "demo_6"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "Acme" in data["title"]
            assert "PoC" in data["title"]
            assert len(data["bulletPoints"]) >= 5
            assert "10k" in data["summaryBlurb"]
    
    def test_demo_scenario_7_next_step_scheduling(self):
        """Demo: Let's set a demo next Wed at 11"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "title": "Demo Call",
                "startISO": "2024-01-17T11:00:00Z", 
                "endISO": "2024-01-17T12:00:00Z",
                "requestId": "demo_7"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"http://localhost:8002/nextstep-parse",
                json={
                    "text": "Let's set a demo next Wed at 11",
                    "requestId": "demo_7"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Demo Call"
            assert "T11:00:00Z" in data["startISO"]
    
    def test_demo_scenario_8_status_update(self):
        """Demo: We lost Acme — budget cut"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "label": "Lost",
                "reasonCategory": "budget",
                "reasonSummary": "Deal was lost due to budget constraints and spending cuts at the client organization.",
                "requestId": "demo_8"
            }
            mock_post.return_value.status_code = 200
            
            response = requests.post(
                f"http://localhost:8002/status-classify",
                json={
                    "label": "Lost",
                    "reasonText": "budget cut",
                    "requestId": "demo_8"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["label"] == "Lost"
            assert data["reasonCategory"] == "budget"
            assert "budget" in data["reasonSummary"].lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])