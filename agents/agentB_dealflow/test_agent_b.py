import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, dealflow_graph, DealflowState, StatusLabel

client = TestClient(app)

class TestDealflowAgent:
    """Test suite for Agent B - Dealflow Agent"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "Agent B" in response.json()["service"]
    
    def test_newlead_full_information(self):
        """Test lead creation with complete information"""
        with patch('app.llm') as mock_llm:
            # Mock LLM response for parsing
            mock_response = Mock()
            mock_response.content = json.dumps({
                "name": "John Smith",
                "company": "Acme Corp",
                "email": "john@acme.com",
                "intent": "PoC development",
                "budget": "around 10k",
                "timeline": "September"
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "raw": "John Smith from Acme Corp wants a PoC in September, budget around 10k, contact him at john@acme.com",
                "requestId": "lead_request_123"
            }
            
            response = client.post("/newlead", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["name"] == "John Smith"
            assert data["company"] == "Acme Corp"
            assert data["email"] == "john@acme.com"
            assert data["intent"] == "PoC development"
            assert data["budget"] == "around 10k"
            assert data["timeline"] == "September"
            assert data["qualityScore"] > 0.8  # Should be high quality
            assert "acme.com" in data["normalizedCompanyDomain"]
            assert data["requestId"] == "lead_request_123"
    
    def test_newlead_minimal_information(self):
        """Test lead creation with minimal information"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "name": None,
                "company": "TechCo",
                "email": None,
                "intent": "needs help",
                "budget": None,
                "timeline": None
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "raw": "Someone from TechCo needs help",
                "requestId": "lead_request_456"
            }
            
            response = client.post("/newlead", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["company"] == "TechCo"
            assert data["intent"] == "needs help"
            assert data["qualityScore"] < 0.5  # Should be lower quality
    
    def test_proposal_copy_generation(self):
        """Test proposal copy generation"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "title": "Custom PoC Development Proposal for Acme Corp",
                "summaryBlurb": "We understand Acme Corp needs a proof of concept solution developed within your September timeline and 10k budget. Our team specializes in rapid prototyping and can deliver a comprehensive PoC that demonstrates the core functionality you require. We'll work closely with your team to ensure the solution meets your specific requirements and provides a clear path to full implementation.",
                "bulletPoints": [
                    "Rapid 4-week development cycle to meet your September deadline",
                    "Dedicated project team with daily progress updates",
                    "Full documentation and handoff materials included",
                    "Budget-conscious approach with transparent pricing",
                    "Post-delivery support and consultation included"
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "lead": {
                    "name": "John Smith",
                    "company": "Acme Corp",
                    "intent": "PoC development",
                    "budget": "around 10k",
                    "timeline": "September"
                },
                "requestId": "proposal_request_123"
            }
            
            response = client.post("/proposal-copy", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Acme Corp" in data["title"]
            assert len(data["summaryBlurb"]) > 100
            assert len(data["bulletPoints"]) >= 3
            assert data["requestId"] == "proposal_request_123"
    
    def test_nextstep_parse_valid(self):
        """Test next step parsing with valid scheduling text"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "title": "Demo Call",
                "startISO": "2024-01-17T11:00:00Z",
                "endISO": "2024-01-17T12:00:00Z"
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "Schedule a demo next Wednesday at 11 AM",
                "requestId": "schedule_request_123"
            }
            
            response = client.post("/nextstep-parse", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["title"] == "Demo Call"
            assert "2024-01-17T11:00:00Z" in data["startISO"]
            assert data["requestId"] == "schedule_request_123"
    
    def test_nextstep_parse_invalid(self):
        """Test next step parsing with invalid text"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "error": "No scheduling information found"
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "I like pizza",
                "requestId": "schedule_request_456"
            }
            
            response = client.post("/nextstep-parse", json=request_data)
            
            assert response.status_code == 400
    
    def test_status_classify_won(self):
        """Test status classification for won deals"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "reasonCategory": "price",
                "reasonSummary": "Client chose us due to competitive pricing and comprehensive feature set."
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "label": "Won",
                "reasonText": "They loved our pricing and features",
                "requestId": "status_request_123"
            }
            
            response = client.post("/status-classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["label"] == "Won"
            assert data["reasonCategory"] == "price"
            assert "pricing" in data["reasonSummary"]
            assert data["requestId"] == "status_request_123"
    
    def test_status_classify_lost(self):
        """Test status classification for lost deals"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "reasonCategory": "budget",
                "reasonSummary": "Client experienced budget cuts and had to postpone the project."
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "label": "Lost",
                "reasonText": "Budget cut",
                "requestId": "status_request_456"
            }
            
            response = client.post("/status-classify", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["label"] == "Lost"
            assert data["reasonCategory"] == "budget"
            assert "budget" in data["reasonSummary"]
    
    def test_parse_lead_node_functionality(self):
        """Test the parse lead node directly"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "name": "Jane Doe",
                "company": "StartupXYZ",
                "intent": "integration help",
                "budget": None,
                "timeline": "ASAP"
            })
            mock_llm.invoke.return_value = mock_response
            
            state = DealflowState(
                messages=[],
                request_id="test_123",
                raw_input="Jane Doe from StartupXYZ needs integration help ASAP"
            )
            
            from app import parse_lead_node
            result = parse_lead_node(state)
            
            assert result["parsed_lead"]["name"] == "Jane Doe"
            assert result["parsed_lead"]["company"] == "StartupXYZ"
            assert result["parsed_lead"]["intent"] == "integration help"
            assert result["parsed_lead"]["timeline"] == "ASAP"
    
    def test_enrich_lead_node_functionality(self):
        """Test the enrich lead node directly"""
        state = DealflowState(
            messages=[],
            request_id="test_123",
            parsed_lead={
                "name": "John Smith",
                "company": "Acme Corp",
                "email": "john@acme.com",
                "intent": "PoC development",
                "budget": "10k"
            }
        )
        
        from app import enrich_lead_node
        result = enrich_lead_node(state)
        
        assert result["enriched_lead"]["name"] == "John Smith"
        assert result["enriched_lead"]["company"] == "Acme Corp"
        assert result["enriched_lead"]["normalizedCompanyDomain"] == "acmecorp.com"
        assert result["enriched_lead"]["email_valid"] is True
        assert result["quality_score"] > 0.8  # High quality lead
    
    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        from app import calculate_lead_quality_score
        
        # High quality lead
        high_quality = {
            "name": "John Smith",
            "company": "Acme Corp", 
            "email": "john@acme.com",
            "intent": "PoC development",
            "budget": "10k"
        }
        score = calculate_lead_quality_score(high_quality)
        assert score >= 0.8
        
        # Low quality lead
        low_quality = {
            "company": "SomeCompany"
        }
        score = calculate_lead_quality_score(low_quality)
        assert score <= 0.5
        
        # Empty lead
        empty_lead = {}
        score = calculate_lead_quality_score(empty_lead)
        assert score == 0.0
    
    def test_extract_domain_from_company(self):
        """Test domain extraction utility"""
        from app import extract_domain_from_company
        
        assert extract_domain_from_company("Acme Corp") == "acmecorp.com"
        assert extract_domain_from_company("TechStart Inc") == "techstart.com"
        assert extract_domain_from_company("Data Solutions LLC") == "datasolutions.com"
        assert extract_domain_from_company("") is None
        assert extract_domain_from_company(None) is None
    
    def test_validate_email(self):
        """Test email validation utility"""
        from app import validate_email
        
        assert validate_email("test@example.com") is True
        assert validate_email("user.name+tag@domain.co.uk") is True
        assert validate_email("invalid-email") is False
        assert validate_email("@domain.com") is False
        assert validate_email("") is False
        assert validate_email(None) is False
    
    def test_graph_routing_newlead(self):
        """Test graph routing for newlead operation"""
        state = DealflowState(
            messages=[],
            request_id="test_123",
            raw_input="Test lead",
            operation="newlead"
        )
        
        # This should route to parse_lead -> enrich_lead
        with patch('app.parse_lead_node') as mock_parse, \
             patch('app.enrich_lead_node') as mock_enrich:
            
            mock_parse.return_value = {**state, "parsed_lead": {"name": "Test"}}
            mock_enrich.return_value = {**state, "enriched_lead": {"name": "Test"}, "quality_score": 0.5}
            
            result = dealflow_graph.invoke(state)
            mock_parse.assert_called_once()
            mock_enrich.assert_called_once()
    
    def test_graph_routing_proposal(self):
        """Test graph routing for proposal operation"""
        state = DealflowState(
            messages=[],
            request_id="test_123",
            operation="proposal",
            enriched_lead={"company": "Test Co"}
        )
        
        # This should route to generate_proposal
        with patch('app.generate_proposal_node') as mock_proposal:
            mock_proposal.return_value = {**state, "proposal_copy": {"title": "Test Proposal"}}
            
            result = dealflow_graph.invoke(state)
            mock_proposal.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])