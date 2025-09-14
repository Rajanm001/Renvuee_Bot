import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
import chromadb

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Agent A - Knowledge Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class IngestRequest(BaseModel):
    driveFileId: str
    requestId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class IngestResponse(BaseModel):
    chunks: int
    tokens: int
    requestId: str
    status: str = "success"

class AskRequest(BaseModel):
    userId: str
    text: str
    requestId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class Citation(BaseModel):
    title: str
    driveFileId: str
    pageRanges: Optional[List[str]] = None
    snippet: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: float
    requestId: str
    status: str = "success"

class FollowupParseRequest(BaseModel):
    text: str
    requestId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class FollowupParseResponse(BaseModel):
    title: str
    startISO: str
    endISO: Optional[str] = None
    attendees: Optional[List[str]] = None
    requestId: str
    status: str = "success"

# LangGraph State
class KnowledgeState(TypedDict):
    messages: Annotated[List[Dict], add_messages]
    request_id: str
    user_id: Optional[str]
    query: Optional[str]
    retrieved_docs: Optional[List[Document]]
    answer: Optional[str]
    citations: Optional[List[Citation]]
    confidence: Optional[float]
    file_id: Optional[str]
    chunks: Optional[int]
    tokens: Optional[int]
    parsed_schedule: Optional[Dict[str, Any]]

# Initialize components
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Use free HuggingFace embeddings instead of OpenAI
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# Use Groq's free LLM API
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    groq_api_key=GROQ_API_KEY,
    max_tokens=1024
)

# Initialize Chroma
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
vectorstore = Chroma(
    client=chroma_client,
    collection_name="knowledge_base",
    embedding_function=embeddings,
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

# LangGraph Nodes
def ingest_node(state: KnowledgeState) -> KnowledgeState:
    """Ingest and process documents into vector store"""
    try:
        file_id = state.get("file_id")
        request_id = state.get("request_id")
        
        if not file_id:
            raise ValueError("No file ID provided")
        
        # Mock file loading - in production, download from Google Drive
        # For demo, assuming file is already accessible locally
        file_path = f"./temp/{file_id}"
        
        # Load document based on file extension
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        else:
            # Fallback to text loading
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                docs = [Document(page_content=content, metadata={"source": file_id})]
        
        if 'docs' not in locals():
            docs = loader.load()
        
        # Add metadata
        for doc in docs:
            doc.metadata.update({
                "drive_file_id": file_id,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id
            })
        
        # Split documents
        chunks = text_splitter.split_documents(docs)
        
        # Add to vector store
        vectorstore.add_documents(chunks)
        
        # Calculate tokens (rough estimate)
        total_tokens = sum(len(chunk.page_content.split()) for chunk in chunks)
        
        logger.info(f"Ingested {len(chunks)} chunks with ~{total_tokens} tokens for file {file_id}")
        
        return {
            **state,
            "chunks": len(chunks),
            "tokens": total_tokens,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in ingest_node: {str(e)}")
        return {
            **state,
            "error": str(e),
            "status": "error"
        }

def retrieve_node(state: KnowledgeState) -> KnowledgeState:
    """Retrieve relevant documents from vector store"""
    try:
        query = state.get("query")
        if not query:
            raise ValueError("No query provided")
        
        # Retrieve relevant documents
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        docs = retriever.get_relevant_documents(query)
        
        logger.info(f"Retrieved {len(docs)} documents for query: {query[:100]}...")
        
        return {
            **state,
            "retrieved_docs": docs
        }
        
    except Exception as e:
        logger.error(f"Error in retrieve_node: {str(e)}")
        return {
            **state,
            "error": str(e),
            "retrieved_docs": []
        }

def answer_node(state: KnowledgeState) -> KnowledgeState:
    """Generate answer based on retrieved documents"""
    try:
        query = state.get("query")
        docs = state.get("retrieved_docs", [])
        
        if not docs:
            return {
                **state,
                "answer": "I couldn't find relevant information in the knowledge base to answer your question.",
                "citations": [],
                "confidence": 0.0
            }
        
        # Prepare context from documents
        context = "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}" for doc in docs])
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a knowledgeable assistant that answers questions based on provided context.
            
Guidelines:
1. Answer concisely and accurately based ONLY on the provided context
2. If the context doesn't contain enough information, say so
3. Always cite your sources by mentioning the document names
4. Provide specific page ranges or sections when available
5. Be honest about confidence level
6. Do not make up information not in the context

Context:
{context}

Question: {question}

Provide your answer with clear citations."""),
            ("human", "{question}")
        ])
        
        # Generate answer
        chain = prompt | llm
        response = chain.invoke({"context": context, "question": query})
        answer = response.content
        
        # Extract citations
        citations = []
        for doc in docs:
            citation = Citation(
                title=doc.metadata.get("source", "Unknown Document"),
                driveFileId=doc.metadata.get("drive_file_id", ""),
                snippet=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            )
            citations.append(citation)
        
        # Calculate confidence (simple heuristic)
        confidence = min(1.0, len(docs) * 0.2)  # More docs = higher confidence, cap at 1.0
        
        logger.info(f"Generated answer with {len(citations)} citations, confidence: {confidence}")
        
        return {
            **state,
            "answer": answer,
            "citations": citations,
            "confidence": confidence
        }
        
    except Exception as e:
        logger.error(f"Error in answer_node: {str(e)}")
        return {
            **state,
            "answer": f"Error generating answer: {str(e)}",
            "citations": [],
            "confidence": 0.0
        }

def parse_schedule_node(state: KnowledgeState) -> KnowledgeState:
    """Parse scheduling information from natural language"""
    try:
        text = state.get("query")
        if not text:
            raise ValueError("No text provided for scheduling parse")
        
        # Create prompt for schedule parsing
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at parsing scheduling information from natural language.

Extract the following information from the user's message:
- title: A brief meeting title
- startISO: Start time in ISO 8601 format (use current date if only time given)
- endISO: End time in ISO 8601 format (optional, default to 1 hour after start)
- attendees: List of mentioned attendee names (optional)

Current date context: {current_date}

Return ONLY a valid JSON object with these fields. If you cannot parse scheduling info, return {{"error": "No scheduling information found"}}.

Examples:
- "Schedule call next Tuesday at 3 PM" -> {{"title": "Scheduled Call", "startISO": "2024-01-16T15:00:00Z", "endISO": "2024-01-16T16:00:00Z"}}
- "Meet with John tomorrow 10 AM about refunds" -> {{"title": "Meeting with John about refunds", "startISO": "2024-01-15T10:00:00Z", "endISO": "2024-01-15T11:00:00Z", "attendees": ["John"]}}
"""),
            ("human", "{text}")
        ])
        
        current_date = datetime.now(timezone.utc).isoformat()
        chain = prompt | llm
        response = chain.invoke({"text": text, "current_date": current_date})
        
        import json
        try:
            parsed_data = json.loads(response.content)
            if "error" in parsed_data:
                return {
                    **state,
                    "parsed_schedule": None,
                    "error": parsed_data["error"]
                }
            
            return {
                **state,
                "parsed_schedule": parsed_data
            }
        except json.JSONDecodeError:
            return {
                **state,
                "parsed_schedule": None,
                "error": "Failed to parse scheduling information"
            }
            
    except Exception as e:
        logger.error(f"Error in parse_schedule_node: {str(e)}")
        return {
            **state,
            "parsed_schedule": None,
            "error": str(e)
        }

# Build LangGraph
def build_knowledge_graph():
    workflow = StateGraph(KnowledgeState)
    
    # Add nodes
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("answer", answer_node)
    workflow.add_node("parse_schedule", parse_schedule_node)
    
    # Define routing logic
    def route_request(state: KnowledgeState):
        if state.get("file_id"):
            return "ingest"
        elif "schedule" in state.get("query", "").lower() or "call" in state.get("query", "").lower():
            return "parse_schedule"
        else:
            return "retrieve"
    
    # Add edges
    workflow.set_conditional_entry_point(route_request)
    workflow.add_edge("ingest", END)
    workflow.add_edge("retrieve", "answer")
    workflow.add_edge("answer", END)
    workflow.add_edge("parse_schedule", END)
    
    return workflow.compile()

knowledge_graph = build_knowledge_graph()

# API Endpoints
@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """Ingest a document from Google Drive into the knowledge base"""
    try:
        logger.info(f"Processing ingest request for file: {request.driveFileId}")
        
        state = KnowledgeState(
            messages=[],
            request_id=request.requestId,
            file_id=request.driveFileId
        )
        
        result = knowledge_graph.invoke(state)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return IngestResponse(
            chunks=result.get("chunks", 0),
            tokens=result.get("tokens", 0),
            requestId=request.requestId
        )
        
    except Exception as e:
        logger.error(f"Error in ingest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Ask a question and get an answer with citations"""
    try:
        logger.info(f"Processing ask request from user {request.userId}: {request.text[:100]}...")
        
        state = KnowledgeState(
            messages=[],
            request_id=request.requestId,
            user_id=request.userId,
            query=request.text
        )
        
        result = knowledge_graph.invoke(state)
        
        return AskResponse(
            answer=result.get("answer", "No answer generated"),
            citations=result.get("citations", []),
            confidence=result.get("confidence", 0.0),
            requestId=request.requestId
        )
        
    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/followup-parse", response_model=FollowupParseResponse)
async def parse_followup(request: FollowupParseRequest):
    """Parse scheduling information from natural language"""
    try:
        logger.info(f"Processing followup parse request: {request.text[:100]}...")
        
        state = KnowledgeState(
            messages=[],
            request_id=request.requestId,
            query=request.text
        )
        
        result = knowledge_graph.invoke(state)
        
        if result.get("error") or not result.get("parsed_schedule"):
            raise HTTPException(status_code=400, detail=result.get("error", "Could not parse scheduling information"))
        
        schedule_data = result["parsed_schedule"]
        
        return FollowupParseResponse(
            title=schedule_data.get("title", "Scheduled Meeting"),
            startISO=schedule_data.get("startISO"),
            endISO=schedule_data.get("endISO"),
            attendees=schedule_data.get("attendees"),
            requestId=request.requestId
        )
        
    except Exception as e:
        logger.error(f"Error in followup-parse endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Agent A - Knowledge"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)