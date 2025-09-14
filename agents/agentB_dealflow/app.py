import os
import uuid
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TypedDict, Annotated, Literal
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
import validators
import phonenumbers

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Agent B - Dealflow Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums and constants
class DealStage(str, Enum):
    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    PROPOSAL = "Proposal"
    NEGOTIATION = "Negotiation"
    WON = "Won"
    LOST = "Lost"
    ON_HOLD = "On Hold"

class StatusLabel(str, Enum):
    WON = "Won"
    LOST = "Lost"
    ON_HOLD = "On hold"

# Pydantic models
class NewLeadRequest(BaseModel):
    raw: str
    requestId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class Lead(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    intent: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    notes: Optional[str] = None

class NewLeadResponse(BaseModel):
    name: Optional[str]
    company: Optional[str] 
    email: Optional[str]
    phone: Optional[str]
    intent: Optional[str]
    budget: Optional[str]
    timeline: Optional[str]
    normalizedCompanyDomain: Optional[str]
    qualityScore: float
    notes: Optional[str]
    requestId: str
    status: str = "success"

class ProposalCopyRequest(BaseModel):
    lead: Lead
    requestId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class ProposalCopyResponse(BaseModel):
    title: str
    summaryBlurb: str
    bulletPoints: List[str]
    requestId: str
    status: str = "success"

class NextStepParseRequest(BaseModel):
    text: str
    requestId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class NextStepParseResponse(BaseModel):
    title: str
    startISO: str
    endISO: Optional[str] = None
    requestId: str
    status: str = "success"

class StatusClassifyRequest(BaseModel):
    label: StatusLabel
    reasonText: Optional[str] = None
    requestId: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class StatusClassifyResponse(BaseModel):
    label: StatusLabel
    reasonCategory: str
    reasonSummary: str
    requestId: str
    status: str = "success"

# LangGraph State
class DealflowState(TypedDict):
    messages: Annotated[List[Dict], add_messages]
    request_id: str
    raw_input: Optional[str]
    parsed_lead: Optional[Dict[str, Any]]
    enriched_lead: Optional[Dict[str, Any]]
    proposal_copy: Optional[Dict[str, Any]]
    parsed_schedule: Optional[Dict[str, Any]]
    status_classification: Optional[Dict[str, Any]]
    quality_score: Optional[float]
    error: Optional[str]

# Initialize components
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    groq_api_key=GROQ_API_KEY,
    max_tokens=1024
)

# Utility functions
def extract_domain_from_company(company_name: str) -> Optional[str]:
    """Extract domain from company name using simple heuristics"""
    if not company_name:
        return None
    
    # Simple domain guessing
    company_clean = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
    company_clean = company_clean.replace(' ', '').replace('inc', '').replace('llc', '').replace('corp', '')
    
    # Try common patterns
    potential_domains = [
        f"{company_clean}.com",
        f"{company_clean}.io", 
        f"{company_clean}.net",
        f"{company_clean}.org"
    ]
    
    # Return the .com version as most likely
    return potential_domains[0] if potential_domains else None

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    try:
        parsed = phonenumbers.parse(phone, None)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

def calculate_lead_quality_score(lead_data: Dict[str, Any]) -> float:
    """Calculate quality score for a lead based on available information"""
    score = 0.0
    
    # Name present (20%)
    if lead_data.get("name"):
        score += 0.2
    
    # Company present (25%)
    if lead_data.get("company"):
        score += 0.25
    
    # Contact info (email or phone) (20%)
    if lead_data.get("email") or lead_data.get("phone"):
        score += 0.2
    
    # Intent/need described (20%)
    if lead_data.get("intent"):
        score += 0.2
    
    # Budget mentioned (15%)
    if lead_data.get("budget"):
        score += 0.15
    
    return min(1.0, score)

# LangGraph Nodes
def parse_lead_node(state: DealflowState) -> DealflowState:
    """Parse lead information from raw text"""
    try:
        raw_input = state.get("raw_input")
        if not raw_input:
            raise ValueError("No raw input provided")
        
        # Create prompt for lead parsing
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting lead information from natural language sales conversations.

Extract the following information from the user's message:
- name: Contact person's name
- company: Company name
- email: Email address (if mentioned)
- phone: Phone number (if mentioned) 
- intent: What they want/need (brief description)
- budget: Budget amount or range (if mentioned)
- timeline: When they need it (if mentioned)
- notes: Any additional relevant context

Return ONLY a valid JSON object with these fields. Use null for missing information.
Be conservative - only extract information that is clearly stated.

Examples:
- "John from Acme Corp wants a PoC in September, budget around 10k" 
  -> {{"name": "John", "company": "Acme Corp", "intent": "PoC", "budget": "around 10k", "timeline": "September"}}
- "sarah.jones@techco.com needs integration help ASAP" 
  -> {{"name": null, "company": "TechCo", "email": "sarah.jones@techco.com", "intent": "integration help", "timeline": "ASAP"}}
"""),
            ("human", "{raw_input}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({"raw_input": raw_input})
        
        import json
        try:
            parsed_lead = json.loads(response.content)
            logger.info(f"Parsed lead: {parsed_lead}")
            
            return {
                **state,
                "parsed_lead": parsed_lead
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse lead JSON: {e}")
            return {
                **state,
                "error": f"Failed to parse lead information: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in parse_lead_node: {str(e)}")
        return {
            **state,
            "error": str(e)
        }

def enrich_lead_node(state: DealflowState) -> DealflowState:
    """Enrich and validate lead information"""
    try:
        parsed_lead = state.get("parsed_lead", {})
        if not parsed_lead:
            return {
                **state,
                "error": "No parsed lead data to enrich"
            }
        
        enriched_lead = parsed_lead.copy()
        
        # Normalize company domain
        if enriched_lead.get("company"):
            domain = extract_domain_from_company(enriched_lead["company"])
            enriched_lead["normalizedCompanyDomain"] = domain
        
        # Validate email
        if enriched_lead.get("email"):
            if not validate_email(enriched_lead["email"]):
                enriched_lead["email_valid"] = False
            else:
                enriched_lead["email_valid"] = True
        
        # Validate phone
        if enriched_lead.get("phone"):
            if not validate_phone(enriched_lead["phone"]):
                enriched_lead["phone_valid"] = False
            else:
                enriched_lead["phone_valid"] = True
        
        # Calculate quality score
        quality_score = calculate_lead_quality_score(enriched_lead)
        
        logger.info(f"Enriched lead with quality score: {quality_score}")
        
        return {
            **state,
            "enriched_lead": enriched_lead,
            "quality_score": quality_score
        }
        
    except Exception as e:
        logger.error(f"Error in enrich_lead_node: {str(e)}")
        return {
            **state,
            "error": str(e)
        }

def generate_proposal_node(state: DealflowState) -> DealflowState:
    """Generate proposal copy based on lead information"""
    try:
        lead_data = state.get("enriched_lead") or state.get("parsed_lead", {})
        if not lead_data:
            return {
                **state,
                "error": "No lead data available for proposal generation"
            }
        
        # Create prompt for proposal generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at writing compelling business proposals. 

Create a professional proposal for the given lead information:

Lead Details:
Company: {company}
Contact: {name}
Intent/Need: {intent}
Budget: {budget}
Timeline: {timeline}

Generate:
1. title: A clear, professional proposal title
2. summaryBlurb: 120-160 words executive summary that addresses their specific need
3. bulletPoints: 3-5 key value propositions as bullet points

Keep the tone professional but warm. Focus on their specific needs and timeline.
Avoid making commitments you cannot fulfill.

Return ONLY a valid JSON object with title, summaryBlurb, and bulletPoints fields.
"""),
            ("human", "Generate proposal for this lead")
        ])
        
        chain = prompt | llm
        response = chain.invoke({
            "company": lead_data.get("company", "Your Organization"),
            "name": lead_data.get("name", ""),
            "intent": lead_data.get("intent", "business solution"),
            "budget": lead_data.get("budget", "to be discussed"),
            "timeline": lead_data.get("timeline", "as soon as possible")
        })
        
        import json
        try:
            proposal_copy = json.loads(response.content)
            logger.info(f"Generated proposal: {proposal_copy.get('title', 'Untitled')}")
            
            return {
                **state,
                "proposal_copy": proposal_copy
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse proposal JSON: {e}")
            return {
                **state,
                "error": f"Failed to generate proposal: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in generate_proposal_node: {str(e)}")
        return {
            **state,
            "error": str(e)
        }

def parse_next_step_node(state: DealflowState) -> DealflowState:
    """Parse next step scheduling information"""
    try:
        text = state.get("raw_input")
        if not text:
            raise ValueError("No text provided for next step parsing")
        
        # Create prompt for next step parsing
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at parsing scheduling information from natural language.

Extract meeting/call scheduling information:
- title: Brief meeting title (focus on business context)
- startISO: Start time in ISO 8601 format
- endISO: End time in ISO 8601 format (default to 1 hour if not specified)

Current date context: {current_date}

For business contexts, infer appropriate titles like:
- "Demo call", "Discovery call", "Follow-up meeting", "Proposal review", etc.

Return ONLY a valid JSON object. If no scheduling info found, return {{"error": "No scheduling information found"}}.

Examples:
- "Schedule a demo next Wed at 11" -> {{"title": "Demo Call", "startISO": "2024-01-17T11:00:00Z", "endISO": "2024-01-17T12:00:00Z"}}
- "Let's have a follow-up call tomorrow 2 PM" -> {{"title": "Follow-up Call", "startISO": "2024-01-16T14:00:00Z", "endISO": "2024-01-16T15:00:00Z"}}
"""),
            ("human", "{text}")
        ])
        
        current_date = datetime.now(timezone.utc).isoformat()
        chain = prompt | llm
        response = chain.invoke({"text": text, "current_date": current_date})
        
        import json
        try:
            parsed_schedule = json.loads(response.content)
            if "error" in parsed_schedule:
                return {
                    **state,
                    "error": parsed_schedule["error"]
                }
            
            logger.info(f"Parsed schedule: {parsed_schedule.get('title', 'No title')}")
            
            return {
                **state,
                "parsed_schedule": parsed_schedule
            }
        except json.JSONDecodeError as e:
            return {
                **state,
                "error": f"Failed to parse scheduling information: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in parse_next_step_node: {str(e)}")
        return {
            **state,
            "error": str(e)
        }

def classify_status_node(state: DealflowState) -> DealflowState:
    """Classify deal status and reason"""
    try:
        label = state.get("status_label")
        reason_text = state.get("reason_text", "")
        
        if not label:
            raise ValueError("No status label provided")
        
        # Create prompt for status classification
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at categorizing deal outcomes and reasons.

Given a deal status ({label}) and reason text, categorize the reason and provide a summary.

For "Won" deals, common categories: price, features, relationship, timeline, competition
For "Lost" deals, common categories: budget, timeline, competition, features, fit, decision
For "On hold" deals, common categories: budget_review, internal_approval, timing, priorities

Provide:
- reasonCategory: One of the categories above (or create appropriate category)
- reasonSummary: 1-2 sentence summary of the situation

Return ONLY a valid JSON object with reasonCategory and reasonSummary fields.
"""),
            ("human", "Status: {label}\nReason: {reason_text}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({"label": label, "reason_text": reason_text})
        
        import json
        try:
            classification = json.loads(response.content)
            classification["label"] = label  # Ensure label is included
            
            logger.info(f"Classified status: {label} - {classification.get('reasonCategory', 'unknown')}")
            
            return {
                **state,
                "status_classification": classification
            }
        except json.JSONDecodeError as e:
            return {
                **state,
                "error": f"Failed to classify status: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in classify_status_node: {str(e)}")
        return {
            **state,
            "error": str(e)
        }

# Build LangGraph
def build_dealflow_graph():
    workflow = StateGraph(DealflowState)
    
    # Add nodes
    workflow.add_node("parse_lead", parse_lead_node)
    workflow.add_node("enrich_lead", enrich_lead_node)
    workflow.add_node("generate_proposal", generate_proposal_node)
    workflow.add_node("parse_next_step", parse_next_step_node)
    workflow.add_node("classify_status", classify_status_node)
    
    # Define routing logic
    def route_request(state: DealflowState):
        if state.get("operation") == "newlead":
            return "parse_lead"
        elif state.get("operation") == "proposal":
            return "generate_proposal"
        elif state.get("operation") == "nextstep":
            return "parse_next_step"
        elif state.get("operation") == "status":
            return "classify_status"
        else:
            return "parse_lead"  # Default
    
    # Add edges
    workflow.set_conditional_entry_point(route_request)
    workflow.add_edge("parse_lead", "enrich_lead")
    workflow.add_edge("enrich_lead", END)
    workflow.add_edge("generate_proposal", END)
    workflow.add_edge("parse_next_step", END)
    workflow.add_edge("classify_status", END)
    
    return workflow.compile()

dealflow_graph = build_dealflow_graph()

# API Endpoints
@app.post("/newlead", response_model=NewLeadResponse)
async def create_new_lead(request: NewLeadRequest):
    """Parse and enrich a new lead from raw text"""
    try:
        logger.info(f"Processing new lead request: {request.raw[:100]}...")
        
        state = DealflowState(
            messages=[],
            request_id=request.requestId,
            raw_input=request.raw,
            operation="newlead"
        )
        
        result = dealflow_graph.invoke(state)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        enriched_lead = result.get("enriched_lead", {})
        quality_score = result.get("quality_score", 0.0)
        
        return NewLeadResponse(
            name=enriched_lead.get("name"),
            company=enriched_lead.get("company"),
            email=enriched_lead.get("email"),
            phone=enriched_lead.get("phone"),
            intent=enriched_lead.get("intent"),
            budget=enriched_lead.get("budget"),
            timeline=enriched_lead.get("timeline"),
            normalizedCompanyDomain=enriched_lead.get("normalizedCompanyDomain"),
            qualityScore=quality_score,
            notes=enriched_lead.get("notes"),
            requestId=request.requestId
        )
        
    except Exception as e:
        logger.error(f"Error in newlead endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/proposal-copy", response_model=ProposalCopyResponse)
async def generate_proposal_copy(request: ProposalCopyRequest):
    """Generate proposal copy for a lead"""
    try:
        logger.info(f"Generating proposal for company: {request.lead.company}")
        
        state = DealflowState(
            messages=[],
            request_id=request.requestId,
            enriched_lead=request.lead.dict(),
            operation="proposal"
        )
        
        result = dealflow_graph.invoke(state)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        proposal_copy = result.get("proposal_copy", {})
        
        return ProposalCopyResponse(
            title=proposal_copy.get("title", "Business Proposal"),
            summaryBlurb=proposal_copy.get("summaryBlurb", ""),
            bulletPoints=proposal_copy.get("bulletPoints", []),
            requestId=request.requestId
        )
        
    except Exception as e:
        logger.error(f"Error in proposal-copy endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nextstep-parse", response_model=NextStepParseResponse)
async def parse_next_step(request: NextStepParseRequest):
    """Parse next step scheduling information from natural language"""
    try:
        logger.info(f"Parsing next step: {request.text[:100]}...")
        
        state = DealflowState(
            messages=[],
            request_id=request.requestId,
            raw_input=request.text,
            operation="nextstep"
        )
        
        result = dealflow_graph.invoke(state)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        parsed_schedule = result.get("parsed_schedule", {})
        
        return NextStepParseResponse(
            title=parsed_schedule.get("title", "Scheduled Meeting"),
            startISO=parsed_schedule.get("startISO"),
            endISO=parsed_schedule.get("endISO"),
            requestId=request.requestId
        )
        
    except Exception as e:
        logger.error(f"Error in nextstep-parse endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/status-classify", response_model=StatusClassifyResponse)
async def classify_status(request: StatusClassifyRequest):
    """Classify deal status and categorize reason"""
    try:
        logger.info(f"Classifying status: {request.label}")
        
        state = DealflowState(
            messages=[],
            request_id=request.requestId,
            status_label=request.label,
            reason_text=request.reasonText,
            operation="status"
        )
        
        result = dealflow_graph.invoke(state)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        classification = result.get("status_classification", {})
        
        return StatusClassifyResponse(
            label=request.label,
            reasonCategory=classification.get("reasonCategory", "unknown"),
            reasonSummary=classification.get("reasonSummary", "No reason provided"),
            requestId=request.requestId
        )
        
    except Exception as e:
        logger.error(f"Error in status-classify endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Agent B - Dealflow"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)