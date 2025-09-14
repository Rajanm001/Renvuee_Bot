import os
import uuid
import logging
import re
from typing import List, Dict, Any, Optional, TypedDict, Annotated, Literal
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Intent Classifier Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class IntentType(str, Enum):
    KNOWLEDGE_QA = "knowledge_qa"
    LEAD_CAPTURE = "lead_capture"
    PROPOSAL_REQUEST = "proposal_request"
    NEXT_STEP = "next_step"
    STATUS_UPDATE = "status_update"
    SMALLTALK = "smalltalk"
    UNKNOWN = "unknown"

# Pydantic models
class Entity(BaseModel):
    type: str
    value: str
    confidence: float

class ClassifyRequest(BaseModel):
    text: str
    hasAttachments: bool = False
    userId: str
    requestId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class ClassifyResponse(BaseModel):
    intent: IntentType
    confidence: float
    entities: List[Entity]
    suggestedAgent: str  # "agentA" or "agentB"
    requestId: str
    status: str = "success"

# LangGraph State
class ClassifierState(TypedDict):
    messages: Annotated[List[Dict], add_messages]
    request_id: str
    user_id: str
    text: str
    has_attachments: bool
    intent: Optional[str]
    confidence: Optional[float]
    entities: Optional[List[Dict[str, Any]]]
    suggested_agent: Optional[str]

# Initialize components
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    groq_api_key=GROQ_API_KEY,
    max_tokens=512
)

# Intent classification patterns (for fast pre-filtering)
INTENT_PATTERNS = {
    IntentType.KNOWLEDGE_QA: [
        r'\b(?:what|how|when|where|why|explain|tell me|describe)\b',
        r'\bpolicy\b',
        r'\brefund\b',
        r'\bhelp\b',
        r'\bquestion\b',
        r'\binformation\b'
    ],
    IntentType.LEAD_CAPTURE: [
        r'\b(?:wants?|needs?|looking for|interested in)\b',
        r'\b(?:poc|proof of concept|demo|trial)\b',
        r'\b(?:budget|price|cost)\b',
        r'\b(?:from|at)\s+\w+(?:\s+(?:corp|inc|llc|ltd|company))?\b',
        r'\b\w+@\w+\.\w+\b',  # email pattern
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # phone pattern
    ],
    IntentType.PROPOSAL_REQUEST: [
        r'\b(?:proposal|quote|estimate|pricing)\b',
        r'\b(?:draft|create|generate|write)\b.*\b(?:proposal|quote)\b',
        r'\bsend.*(?:proposal|quote)\b'
    ],
    IntentType.NEXT_STEP: [
        r'\b(?:schedule|meeting|call|demo)\b',
        r'\b(?:tomorrow|today|next|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        r'\b(?:\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm))\b',
        r'\b(?:let\'s|set up|arrange)\b'
    ],
    IntentType.STATUS_UPDATE: [
        r'\b(?:won|lost|closed|signed|cancelled)\b',
        r'\b(?:update|status|progress)\b',
        r'\b(?:decided|chose|selected|rejected)\b',
        r'\b(?:budget cut|no budget|postponed)\b'
    ],
    IntentType.SMALLTALK: [
        r'\b(?:hello|hi|hey|thanks|thank you|bye|goodbye)\b',
        r'\b(?:how are you|good morning|good afternoon)\b',
        r'\b(?:nice|great|awesome|cool)\b'
    ]
}

def quick_intent_check(text: str, has_attachments: bool) -> IntentType:
    """Quick pattern-based intent detection"""
    if has_attachments:
        return IntentType.KNOWLEDGE_QA
    
    text_lower = text.lower()
    
    # Count pattern matches for each intent
    intent_scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                score += 1
        intent_scores[intent] = score
    
    # Return intent with highest score, or unknown if no matches
    if max(intent_scores.values()) == 0:
        return IntentType.UNKNOWN
    
    return max(intent_scores, key=intent_scores.get)

# LangGraph Nodes
def classify_intent_node(state: ClassifierState) -> ClassifierState:
    """Classify intent using LLM with structured output"""
    try:
        text = state.get("text")
        has_attachments = state.get("has_attachments", False)
        
        if not text:
            raise ValueError("No text provided for classification")
        
        # Quick pre-filter
        quick_intent = quick_intent_check(text, has_attachments)
        
        # Create prompt for detailed classification
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert intent classifier for a business communication system.

Classify the user's message into one of these intents:
- knowledge_qa: Questions about policies, procedures, or information requests
- lead_capture: New business leads, prospects, or potential customers
- proposal_request: Requests for proposals, quotes, or estimates  
- next_step: Scheduling meetings, calls, or follow-ups
- status_update: Updates on deal status (won/lost/on-hold)
- smalltalk: Greetings, thanks, casual conversation
- unknown: Cannot determine intent clearly

Also extract entities:
- names: Person names mentioned
- companies: Company/organization names
- emails: Email addresses
- phones: Phone numbers
- dates: Date/time references
- money: Budget/price mentions

Context:
- User has attachments: {has_attachments}
- Quick pre-filter suggests: {quick_intent}

Return ONLY a valid JSON object with:
{{
  "intent": "one_of_the_intents_above",
  "confidence": 0.0-1.0,
  "entities": [
    {{"type": "name", "value": "John Smith", "confidence": 0.9}},
    {{"type": "company", "value": "Acme Corp", "confidence": 0.8}}
  ]
}}

Message to classify: "{text}"
"""),
            ("human", "Classify this message")
        ])
        
        chain = prompt | llm
        response = chain.invoke({
            "text": text, 
            "has_attachments": has_attachments,
            "quick_intent": quick_intent.value
        })
        
        import json
        try:
            result = json.loads(response.content)
            
            intent = result.get("intent", "unknown")
            confidence = result.get("confidence", 0.0)
            entities = result.get("entities", [])
            
            # Determine suggested agent
            if intent in ["knowledge_qa"]:
                suggested_agent = "agentA"
            elif intent in ["lead_capture", "proposal_request", "next_step", "status_update"]:
                suggested_agent = "agentB"
            else:
                suggested_agent = "agentB"  # Default to dealflow for ambiguous cases
            
            logger.info(f"Classified intent: {intent} (confidence: {confidence}) -> {suggested_agent}")
            
            return {
                **state,
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "suggested_agent": suggested_agent
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification JSON: {e}")
            # Fallback to quick classification
            return {
                **state,
                "intent": quick_intent.value,
                "confidence": 0.6,
                "entities": [],
                "suggested_agent": "agentB" if quick_intent != IntentType.KNOWLEDGE_QA else "agentA"
            }
            
    except Exception as e:
        logger.error(f"Error in classify_intent_node: {str(e)}")
        return {
            **state,
            "intent": "unknown",
            "confidence": 0.0,
            "entities": [],
            "suggested_agent": "agentB",
            "error": str(e)
        }

def extract_entities_node(state: ClassifierState) -> ClassifierState:
    """Additional entity extraction and validation"""
    try:
        text = state.get("text", "")
        entities = state.get("entities", [])
        
        # Add simple regex-based entity extraction as backup
        additional_entities = []
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails:
            if not any(e["type"] == "email" and e["value"] == email for e in entities):
                additional_entities.append({
                    "type": "email",
                    "value": email,
                    "confidence": 0.9
                })
        
        # Phone extraction (simple)
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        phones = re.findall(phone_pattern, text)
        for phone_parts in phones:
            phone = f"({phone_parts[0]}) {phone_parts[1]}-{phone_parts[2]}"
            if not any(e["type"] == "phone" and phone_parts[0] in e["value"] for e in entities):
                additional_entities.append({
                    "type": "phone",
                    "value": phone,
                    "confidence": 0.8
                })
        
        # Money/budget extraction
        money_pattern = r'\$[\d,]+|\b\d+k?\b.*(?:budget|dollar|usd|cost|price)'
        money_matches = re.findall(money_pattern, text.lower())
        for money in money_matches:
            if not any(e["type"] == "money" for e in entities):
                additional_entities.append({
                    "type": "money",
                    "value": money,
                    "confidence": 0.7
                })
        
        # Combine entities
        all_entities = entities + additional_entities
        
        return {
            **state,
            "entities": all_entities
        }
        
    except Exception as e:
        logger.error(f"Error in extract_entities_node: {str(e)}")
        return state

# Build LangGraph
def build_classifier_graph():
    workflow = StateGraph(ClassifierState)
    
    # Add nodes
    workflow.add_node("classify", classify_intent_node)
    workflow.add_node("extract", extract_entities_node)
    
    # Add edges
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "extract")
    workflow.add_edge("extract", END)
    
    return workflow.compile()

classifier_graph = build_classifier_graph()

# API Endpoints
@app.post("/classify", response_model=ClassifyResponse)
async def classify_intent(request: ClassifyRequest):
    """Classify user intent and extract entities"""
    try:
        logger.info(f"Classifying message from user {request.userId}: {request.text[:100]}...")
        
        state = ClassifierState(
            messages=[],
            request_id=request.requestId,
            user_id=request.userId,
            text=request.text,
            has_attachments=request.hasAttachments
        )
        
        result = classifier_graph.invoke(state)
        
        if result.get("error"):
            logger.warning(f"Classification error: {result['error']}")
            # Still return result with fallback values
        
        # Convert entities to Pydantic models
        entities = []
        for entity_dict in result.get("entities", []):
            entities.append(Entity(
                type=entity_dict["type"],
                value=entity_dict["value"],
                confidence=entity_dict["confidence"]
            ))
        
        return ClassifyResponse(
            intent=IntentType(result.get("intent", "unknown")),
            confidence=result.get("confidence", 0.0),
            entities=entities,
            suggestedAgent=result.get("suggested_agent", "agentB"),
            requestId=request.requestId
        )
        
    except Exception as e:
        logger.error(f"Error in classify endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Intent Classifier"}

# Additional utility endpoints for testing
@app.post("/quick-classify")
async def quick_classify(request: ClassifyRequest):
    """Quick pattern-based classification (no LLM)"""
    try:
        intent = quick_intent_check(request.text, request.hasAttachments)
        
        return {
            "intent": intent.value,
            "confidence": 0.7,
            "entities": [],
            "suggestedAgent": "agentA" if intent == IntentType.KNOWLEDGE_QA else "agentB",
            "requestId": request.requestId,
            "method": "pattern_based"
        }
        
    except Exception as e:
        logger.error(f"Error in quick-classify endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)