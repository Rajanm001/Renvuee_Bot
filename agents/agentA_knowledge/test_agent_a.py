import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, knowledge_graph, KnowledgeState

client = TestClient(app)

class TestKnowledgeAgent:
    """Test suite for Agent A - Knowledge Agent"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "Agent A" in response.json()["service"]
    
    @patch('app.vectorstore')
    @patch('app.PyPDFLoader')
    def test_ingest_pdf_document(self, mock_pdf_loader, mock_vectorstore):
        """Test PDF document ingestion"""
        # Mock PDF loader
        mock_doc = Mock()
        mock_doc.page_content = "This is test content from a PDF document."
        mock_doc.metadata = {"source": "test.pdf"}
        mock_pdf_loader.return_value.load.return_value = [mock_doc]
        
        # Mock vectorstore
        mock_vectorstore.add_documents.return_value = None
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            request_data = {
                "driveFileId": "test_pdf_123",
                "requestId": "test_request_123"
            }
            
            response = client.post("/ingest", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["chunks"] > 0
            assert data["tokens"] > 0
            assert data["requestId"] == "test_request_123"
    
    @patch('app.vectorstore')
    def test_ask_question_with_results(self, mock_vectorstore):
        """Test asking a question with mock retrieval results"""
        # Mock retriever and documents
        mock_doc = Mock()
        mock_doc.page_content = "Our refund policy allows returns within 30 days of purchase."
        mock_doc.metadata = {"source": "refund_policy.pdf", "drive_file_id": "doc_123"}
        
        mock_retriever = Mock()
        mock_retriever.get_relevant_documents.return_value = [mock_doc]
        mock_vectorstore.as_retriever.return_value = mock_retriever
        
        # Mock LLM response
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "According to our refund policy document, customers can return items within 30 days of purchase for a full refund."
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "userId": "user123",
                "text": "What is your refund policy?",
                "requestId": "ask_request_123"
            }
            
            response = client.post("/ask", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "refund" in data["answer"].lower()
            assert len(data["citations"]) > 0
            assert data["confidence"] > 0
            assert data["requestId"] == "ask_request_123"
    
    @patch('app.vectorstore')
    def test_ask_question_no_results(self, mock_vectorstore):
        """Test asking a question with no retrieval results"""
        # Mock empty retrieval
        mock_retriever = Mock()
        mock_retriever.get_relevant_documents.return_value = []
        mock_vectorstore.as_retriever.return_value = mock_retriever
        
        request_data = {
            "userId": "user123",
            "text": "What is the meaning of life?",
            "requestId": "ask_request_456"
        }
        
        response = client.post("/ask", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "couldn't find" in data["answer"]
        assert len(data["citations"]) == 0
        assert data["confidence"] == 0.0
    
    def test_followup_parse_valid_schedule(self):
        """Test parsing valid scheduling text"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "title": "Meeting with Dana about refunds",
                "startISO": "2024-01-16T10:00:00Z",
                "endISO": "2024-01-16T11:00:00Z",
                "attendees": ["Dana"]
            })
            mock_llm.invoke.return_value = mock_response
            
            request_data = {
                "text": "Schedule a call next Tue at 10:00 with Dana about refunds",
                "requestId": "schedule_request_123"
            }
            
            response = client.post("/followup-parse", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Dana" in data["title"]
            assert "refunds" in data["title"]
            assert data["startISO"] == "2024-01-16T10:00:00Z"
            assert data["attendees"] == ["Dana"]
    
    def test_followup_parse_invalid_schedule(self):
        """Test parsing invalid scheduling text"""
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
            
            response = client.post("/followup-parse", json=request_data)
            
            assert response.status_code == 400
    
    def test_ingest_node_functionality(self):
        """Test the ingest node directly"""
        with patch('app.PyPDFLoader') as mock_loader, \
             patch('app.vectorstore') as mock_vectorstore, \
             patch('os.path.exists', return_value=True):
            
            # Mock document loading
            mock_doc = Mock()
            mock_doc.page_content = "Test content"
            mock_doc.metadata = {"source": "test.pdf"}
            mock_loader.return_value.load.return_value = [mock_doc]
            
            state = KnowledgeState(
                messages=[],
                request_id="test_123",
                file_id="test_file.pdf"
            )
            
            from app import ingest_node
            result = ingest_node(state)
            
            assert result["status"] == "success"
            assert result["chunks"] > 0
            assert result["tokens"] > 0
    
    def test_retrieve_node_functionality(self):
        """Test the retrieve node directly"""
        with patch('app.vectorstore') as mock_vectorstore:
            # Mock retriever
            mock_doc = Mock()
            mock_doc.page_content = "Test retrieved content"
            mock_doc.metadata = {"source": "test.pdf"}
            
            mock_retriever = Mock()
            mock_retriever.get_relevant_documents.return_value = [mock_doc]
            mock_vectorstore.as_retriever.return_value = mock_retriever
            
            state = KnowledgeState(
                messages=[],
                request_id="test_123",
                query="test query"
            )
            
            from app import retrieve_node
            result = retrieve_node(state)
            
            assert len(result["retrieved_docs"]) > 0
            assert result["retrieved_docs"][0].page_content == "Test retrieved content"
    
    def test_answer_node_functionality(self):
        """Test the answer node directly"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "This is a test answer based on the provided context."
            mock_llm.invoke.return_value = mock_response
            
            # Mock retrieved documents
            mock_doc = Mock()
            mock_doc.page_content = "Test context content"
            mock_doc.metadata = {"source": "test.pdf", "drive_file_id": "123"}
            
            state = KnowledgeState(
                messages=[],
                request_id="test_123",
                query="test question",
                retrieved_docs=[mock_doc]
            )
            
            from app import answer_node
            result = answer_node(state)
            
            assert result["answer"] == "This is a test answer based on the provided context."
            assert len(result["citations"]) > 0
            assert result["confidence"] > 0
    
    def test_parse_schedule_node_functionality(self):
        """Test the parse schedule node directly"""
        with patch('app.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "title": "Test Meeting",
                "startISO": "2024-01-16T14:00:00Z",
                "endISO": "2024-01-16T15:00:00Z"
            })
            mock_llm.invoke.return_value = mock_response
            
            state = KnowledgeState(
                messages=[],
                request_id="test_123",
                query="Schedule a meeting tomorrow at 2 PM"
            )
            
            from app import parse_schedule_node
            result = parse_schedule_node(state)
            
            assert result["parsed_schedule"]["title"] == "Test Meeting"
            assert "2024-01-16T14:00:00Z" in result["parsed_schedule"]["startISO"]
    
    def test_graph_routing_ingest(self):
        """Test graph routing for ingest requests"""
        state = KnowledgeState(
            messages=[],
            request_id="test_123",
            file_id="test_file.pdf"
        )
        
        # This should route to ingest
        with patch('app.ingest_node') as mock_ingest:
            mock_ingest.return_value = {**state, "chunks": 5, "tokens": 100, "status": "success"}
            
            result = knowledge_graph.invoke(state)
            mock_ingest.assert_called_once()
    
    def test_graph_routing_ask(self):
        """Test graph routing for ask requests"""
        state = KnowledgeState(
            messages=[],
            request_id="test_123",
            query="What is your policy?"
        )
        
        # This should route to retrieve -> answer
        with patch('app.retrieve_node') as mock_retrieve, \
             patch('app.answer_node') as mock_answer:
            
            mock_retrieve.return_value = {**state, "retrieved_docs": []}
            mock_answer.return_value = {**state, "answer": "test", "citations": [], "confidence": 0.5}
            
            result = knowledge_graph.invoke(state)
            mock_retrieve.assert_called_once()
            mock_answer.assert_called_once()
    
    def test_graph_routing_schedule(self):
        """Test graph routing for schedule requests"""
        state = KnowledgeState(
            messages=[],
            request_id="test_123",
            query="Schedule a call tomorrow"
        )
        
        # This should route to parse_schedule
        with patch('app.parse_schedule_node') as mock_schedule:
            mock_schedule.return_value = {**state, "parsed_schedule": {"title": "Call"}}
            
            result = knowledge_graph.invoke(state)
            mock_schedule.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])