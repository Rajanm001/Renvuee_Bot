import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, classifier_graph, ClassifierState, IntentType, quick_intent_check

client = TestClient(app)

class TestIntentClassifier:
    """Test suite for Intent Classifier Service"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "Intent Classifier" in response.json()["service"]
    
    def test_classify_knowledge_qa(self):
        """Test classification of knowledge Q&A intent"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "knowledge_qa",
                "confidence": 0.9,
                "entities": [
                    {"type": "topic", "value": "refund policy", "confidence": 0.8}
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "What is your refund policy?",
                "hasAttachments": False,
                "userId": "user123",
                "requestId": "classify_request_123"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["intent"] == "knowledge_qa"
            assert data["suggestedAgent"] == "agentA"
            assert data["confidence"] > 0.8
            assert data["requestId"] == "classify_request_123"
    
    def test_classify_with_attachments(self):
        """Test classification when attachments are present"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "knowledge_qa",
                "confidence": 0.95,
                "entities": []
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "Here's our new document",
                "hasAttachments": True,
                "userId": "user123",
                "requestId": "classify_request_456"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "knowledge_qa"
            assert data["suggestedAgent"] == "agentA"
    
    def test_classify_lead_capture(self):
        """Test classification of lead capture intent"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "lead_capture",
                "confidence": 0.85,
                "entities": [
                    {"type": "name", "value": "John Smith", "confidence": 0.9},
                    {"type": "company", "value": "Acme Corp", "confidence": 0.8},
                    {"type": "money", "value": "10k", "confidence": 0.7}
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "John Smith from Acme Corp wants a PoC, budget around 10k",
                "hasAttachments": False,
                "userId": "user123",
                "requestId": "classify_request_789"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "lead_capture"
            assert data["suggestedAgent"] == "agentB"
            assert len(data["entities"]) >= 3
            
            # Check specific entities
            entity_values = [e["value"] for e in data["entities"]]
            assert "John Smith" in entity_values
            assert "Acme Corp" in entity_values
    
    def test_classify_proposal_request(self):
        """Test classification of proposal request intent"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "proposal_request",
                "confidence": 0.9,
                "entities": [
                    {"type": "company", "value": "Acme", "confidence": 0.8}
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "Can you draft a proposal for Acme?",
                "hasAttachments": False,
                "userId": "user123"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "proposal_request"
            assert data["suggestedAgent"] == "agentB"
    
    def test_classify_next_step(self):
        """Test classification of next step scheduling intent"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "next_step",
                "confidence": 0.88,
                "entities": [
                    {"type": "date", "value": "next Wednesday", "confidence": 0.9},
                    {"type": "time", "value": "11 AM", "confidence": 0.8}
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "Let's schedule a demo next Wednesday at 11 AM",
                "hasAttachments": False,
                "userId": "user123"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "next_step"
            assert data["suggestedAgent"] == "agentB"
    
    def test_classify_status_update(self):
        """Test classification of status update intent"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "status_update",
                "confidence": 0.92,
                "entities": [
                    {"type": "company", "value": "Acme", "confidence": 0.8},
                    {"type": "status", "value": "lost", "confidence": 0.9}
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "We lost the Acme deal - budget cut",
                "hasAttachments": False,
                "userId": "user123"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "status_update"
            assert data["suggestedAgent"] == "agentB"
    
    def test_classify_smalltalk(self):
        """Test classification of smalltalk intent"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "smalltalk",
                "confidence": 0.95,
                "entities": []
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "Hello! How are you today?",
                "hasAttachments": False,
                "userId": "user123"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "smalltalk"
            # Smalltalk defaults to agentB for handling
            assert data["suggestedAgent"] == "agentB"
    
    def test_classify_unknown(self):
        """Test classification of unknown/unclear intent"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "unknown",
                "confidence": 0.3,
                "entities": []
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "Xyz abc def random text",
                "hasAttachments": False,
                "userId": "user123"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "unknown"
            assert data["confidence"] < 0.5
    
    def test_quick_classify_endpoint(self):
        """Test the quick pattern-based classification endpoint"""
        request_data = {
            "text": "What is your refund policy?",
            "hasAttachments": False,
            "userId": "user123"
        }
        
        response = client.post("/quick-classify", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "knowledge_qa"
        assert data["method"] == "pattern_based"
        assert data["confidence"] == 0.7
    
    def test_quick_intent_check_function(self):
        """Test the quick intent detection function"""
        # Knowledge Q&A
        assert quick_intent_check("What is your policy?", False) == IntentType.KNOWLEDGE_QA
        assert quick_intent_check("How does this work?", False) == IntentType.KNOWLEDGE_QA
        assert quick_intent_check("Tell me about refunds", False) == IntentType.KNOWLEDGE_QA
        
        # Lead capture
        assert quick_intent_check("John from Acme wants a demo", False) == IntentType.LEAD_CAPTURE
        assert quick_intent_check("We need a PoC, budget 10k", False) == IntentType.LEAD_CAPTURE
        assert quick_intent_check("Contact me at john@acme.com", False) == IntentType.LEAD_CAPTURE
        
        # Proposal request
        assert quick_intent_check("Can you send a proposal?", False) == IntentType.PROPOSAL_REQUEST
        assert quick_intent_check("Draft a quote for us", False) == IntentType.PROPOSAL_REQUEST
        
        # Next step
        assert quick_intent_check("Schedule a call tomorrow", False) == IntentType.NEXT_STEP
        assert quick_intent_check("Let's meet next Tuesday at 3 PM", False) == IntentType.NEXT_STEP
        
        # Status update
        assert quick_intent_check("We won the deal!", False) == IntentType.STATUS_UPDATE
        assert quick_intent_check("Lost to competitor", False) == IntentType.STATUS_UPDATE
        
        # Smalltalk
        assert quick_intent_check("Hello there!", False) == IntentType.SMALLTALK
        assert quick_intent_check("Thanks for your help", False) == IntentType.SMALLTALK
        
        # Attachment handling
        assert quick_intent_check("Random text", True) == IntentType.KNOWLEDGE_QA
        
        # Unknown
        assert quick_intent_check("Xyz random gibberish", False) == IntentType.UNKNOWN
    
    def test_entity_extraction(self):
        """Test entity extraction functionality"""
        text = "Contact John Smith at john@acme.com or call (555) 123-4567 about the $10k budget"
        
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "lead_capture",
                "confidence": 0.9,
                "entities": [
                    {"type": "name", "value": "John Smith", "confidence": 0.9}
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": text,
                "hasAttachments": False,
                "userId": "user123"
            }
            
            response = client.post("/classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Should extract email and phone via regex backup
            entity_types = [e["type"] for e in data["entities"]]
            entity_values = [e["value"] for e in data["entities"]]
            
            assert "email" in entity_types
            assert "phone" in entity_types
            assert "john@acme.com" in entity_values
            assert any("555" in val for val in entity_values)
    
    def test_graph_execution(self):
        """Test the LangGraph execution directly"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "intent": "knowledge_qa",
                "confidence": 0.9,
                "entities": []
            })
            mock_llm.invoke.return_value = mock_response
            
            state = ClassifierState(
                messages=[],
                request_id="test_123",
                user_id="user123",
                text="What is your policy?",
                has_attachments=False
            )
            
            result = classifier_graph.invoke(state)
            
            assert result["intent"] == "knowledge_qa"
            assert result["confidence"] == 0.9
            assert result["suggested_agent"] == "agentA"
    
    def test_fallback_on_llm_error(self):
        """Test fallback behavior when LLM fails"""
        with patch('app.llm') as mock_llm:
            # Simulate LLM error
            mock_llm.invoke.side_effect = Exception("LLM API error")
            
            request_data = {
                "text": "What is your refund policy?",
                "hasAttachments": False,
                "userId": "user123"
            }
            
            response = client.post("/classify", json=request_data)
            
            # Should still return a response (fallback to pattern matching)
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] in ["knowledge_qa", "unknown"]
            assert data["confidence"] >= 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])