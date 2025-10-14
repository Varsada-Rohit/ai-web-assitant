from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents.feedback_agent import feedback_agent
from agents.action_items_extractor_agent import ActionItemsExtractorResponse, action_items_extractor_agent
from agents.summarise_agent import summarise_agent
from agents.webassistant import web_assistant_agent
from fastapi.responses import StreamingResponse
from models.session import Session
from tools import query_document, read_file
from dotenv import load_dotenv
from datetime import datetime
import json
import asyncio
from contexts.page_context_mapper import get_target_pages

load_dotenv()

print("\n" + "="*60)
print("🚀 AI WEB ASSISTANT STARTING UP")
print("="*60)
print("📡 FastAPI server initializing...")
print("🤖 AI agents loading...")
print("📂 Session management ready...")
print("🔧 Context extractors ready...")
print("="*60)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# FLOW 

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    action_items: Optional[List[Dict[str, Any]]] = None


class ContextPayload(BaseModel):
    distilledNodes: Optional[list]
    mainTree: Optional[list]
    appState: Optional[dict]
    route: Optional[str]

class AgentQuery(BaseModel):
    session_id: str
    question: str
    current_route: str  # NEW: Current page route for context extraction

class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[Message]
    context_available: bool

# Store session data in memory for performance
session_event_locks: Dict[str, asyncio.Lock] = {}
sessions: Dict[str, Session] = {}

def get_or_create_session(session_id: str, user_id: str = None) -> Session:
    """
    Check if session exists in memory, if not create or load it from disk
    """
    if session_id in sessions:
        return sessions[session_id]
    
    # Session not in memory, create or load it
    if user_id is None:
        user_id = session_id  # Use session_id as user_id if not provided
    
    session = Session(user_id=user_id, session_id=session_id)
    sessions[session_id] = session
    return session

def remove_session_from_memory(session_id: str):
    """
    Remove session from memory (but keep it on disk)
    """
    if session_id in sessions:
        del sessions[session_id]

@app.post("/api/update-context")
async def update_context(context: ContextPayload, x_session_id: Optional[str] = Header(None)):
    print(f"\n=== UPDATE CONTEXT REQUEST ===")
    print(f"Session ID: {x_session_id}")
    print(f"Route: {context.route}")
    print(f"Distilled Nodes Count: {len(context.distilledNodes) if context.distilledNodes else 0}")
    print(f"Main Tree Count: {len(context.mainTree) if context.mainTree else 0}")
    
    if not x_session_id:
        print("❌ ERROR: Missing X-Session-Id header")
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header")

    # Import application context and page context mapper
    from contexts.app_context import web_app_context
    from contexts.page_context_mapper import get_page_context

    # Get page-specific context using the mapper
    page_specific_context = get_page_context(context.route)
    print(f"📄 Page context loaded for route: {context.route}")

    print("🤖 Running summarise agent...")
    context_summary = summarise_agent(
        context.dict(),
        application_context=web_app_context,
        page_context=page_specific_context
    )
    print(f"✅ Context summary generated ({len(context_summary.summary)} chars)")

    session = get_or_create_session(x_session_id)
    session.update_current_dom_summary(context_summary.summary)
    session.save()
    print(f"💾 Session updated and saved")

    print("=== CONTEXT UPDATE COMPLETE ===\n")
    return {"status": "success"}

@app.post("/api/update-interaction-dom")
async def update_interaction_dom(interaction_dom: ContextPayload, x_session_id: Optional[str] = Header(None)):
    print(f"\n=== UPDATE INTERACTION DOM REQUEST ===")
    print(f"Session ID: {x_session_id}")
    print(f"Route: {interaction_dom.route}")
    print(f"Distilled Nodes Count: {len(interaction_dom.distilledNodes) if interaction_dom.distilledNodes else 0}")

    if not x_session_id:
        print("❌ ERROR: Missing X-Session-Id header")
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header")
    
    session = get_or_create_session(x_session_id)
    session.update_current_interaction_dom(interaction_dom.dict())
    print(f"🔄 Updated interaction DOM for session: {x_session_id}")
    
    if x_session_id in session_event_locks:
        session_event_locks[x_session_id].set()
        print(f"🔓 Released event lock for session: {x_session_id}")
    session.save()
    print(f"💾 Session saved")
    print("=== INTERACTION DOM UPDATE COMPLETE ===\n")
    return {"status": "success"}

async def generate_action_items(session_data: Session, query: str, feedback: Optional[str] = None) -> ActionItemsExtractorResponse:
    print(f"\n🎯 GENERATING ACTION ITEMS")
    print(f"Session: {session_data.session_id}")
    print(f"Query: {query[:100]}...")
    print(f"Feedback: {feedback[:50] if feedback else 'None'}...")
    
    print('⏳ WAITING FOR RESUME EVENT')
    if session_data.session_id not in session_event_locks:
        session_event_locks[session_data.session_id] = asyncio.Event()
    await session_event_locks[session_data.session_id].wait()
    session_event_locks[session_data.session_id].clear()
    print('✅ RESUME EVENT SET')
    
    context = session_data.current_interaction_dom
    session_data.current_interaction_dom = None
    print(f"📋 Context retrieved for action items generation")

    print("🤖 Running action items extractor agent...")
    action_items = action_items_extractor_agent(context, query,session_data.get_recent_context(),feedback)
    print(f"✅ Generated {len(action_items.action_items)} action items")

    session_data.add_event("assistant", "action_planner_agent", action_items.dict())
    print(f"📝 Event logged for action planner agent")
    
    return action_items

async def generate_streaming_response(query: AgentQuery):
    """Generator function for streaming responses"""
    print(f"\n🚀 STARTING STREAMING RESPONSE")
    print(f"Session ID: {query.session_id}")
    print(f"Question: {query.question[:100]}...")
    print(f"Current Route: {query.current_route}")

    # Always get or create session (don't check if it exists first)
    session_data = get_or_create_session(query.session_id)
    print(f"📂 Session loaded/created: {query.session_id}")

    yield json.dumps({"content": "Processing query", "type": "point"}) + "\n\n"

    session_data.add_event("user", "client", query.question)
    print(f"📝 User event logged")

    # Get conversation history for the agent
    conversation_history = session_data.get_recent_context()
    print(f"📚 Conversation history retrieved ({len(conversation_history)} chars)")

    # Import contexts
    from contexts.app_context import web_app_context
    from contexts.page_context_mapper import get_page_context
    from agents.action_planner_agent import action_planner_agent

    # Get page-specific context based on current route
    page_context = get_page_context(query.current_route)
    target_page_route = get_target_pages(query.question,web_app_context, conversation_history)
    target_page_context = get_page_context(target_page_route)
    print(f"📄 Page context loaded for route: {query.current_route}")

    yield json.dumps({"content": "interaction_dom", "type": "context_request"}) + "\n\n"
    print("🔄 Requesting interaction DOM from client")

    if session_data.session_id not in session_event_locks:
        session_event_locks[session_data.session_id] = asyncio.Event()
    await session_event_locks[session_data.session_id].wait()
    session_event_locks[session_data.session_id].clear()
    print("✅ Interaction DOM received")

    # Generate high-level action plan
    yield json.dumps({"content": "Creating action plan...", "type": "point"}) + "\n\n"
    print("🎯 Creating action plan...")

    action_plan = action_planner_agent(
        user_query=query.question,
        current_route=query.current_route,
        application_context=web_app_context,
        page_context=page_context,
        target_page_context=target_page_context,
        interaction_dom=session_data.current_interaction_dom,
        conversation_history=conversation_history
    )
    print(f"✅ Action plan created with {action_plan.total_steps} steps")

    # Log the plan
    session_data.add_event("assistant", "action_planner", action_plan.dict())
    print(f"📝 Action plan event logged")

    # Stream the plan to user
    yield json.dumps({
        "content": {
            "summary": action_plan.summary,
            "total_steps": action_plan.total_steps,
            "steps": [step.dict() for step in action_plan.plan_steps]
        },
        "type": "action_plan"
    }) + "\n\n"

    # TODO: Continue with DOM execution loop here
    # For now, just acknowledge the plan was created
    yield json.dumps({"content": "Action plan created. Next: DOM execution (to be implemented)", "type": "point"}) + "\n\n"

    # OLD CODE BELOW - TO BE REPLACED WITH NEW BATCHED EXECUTION FLOW
    # Keeping temporarily for reference

    user_query = query.question
    # action_items = None

    # NOTE: This old logic will be replaced with batched DOM executor
    if False:  # Disabled for now
        yield json.dumps({"content": "interaction_dom", "type": "context_request"}) + "\n\n"
        action_items = await generate_action_items(session_data, user_query)
        action_items_dict = [item.dict() for item in action_items.action_items]
        yield json.dumps({"content": {"action_items": action_items_dict, "message": action_items.message}, "type": "action_items"}) + "\n\n"
        
        if len(action_items.action_items) > 0:
            # Convert ActionItem objects to dictionaries for JSON serialization
            # assistant_message.action_items = action_items_dict // TODO: handle later

            is_user_query_fulfilled = False

            while not is_user_query_fulfilled:

                should_wait = True


                while should_wait:
                    await asyncio.sleep(1)

                    if session_data.session_id not in session_event_locks:
                        session_event_locks[session_data.session_id] = asyncio.Event()
                    await session_event_locks[session_data.session_id].wait()
                    session_event_locks[session_data.session_id].clear()
                    context_after_action_items = session_data.current_interaction_dom
                    session_data.current_interaction_dom = None

                    feedback = feedback_agent(action_items.action_items, user_query, context_summary, context_after_action_items, session_data.get_recent_context())
                    print(f"🔄 FEEDBACK AGENT RESULT:")
                    print(f"   Completed: {feedback.isCompleted}")
                    print(f"   Should Wait: {feedback.should_wait}")
                    print(f"   Message: {feedback.message[:100]}...")
                    session_data.add_event("assistant", "feedback_agent", feedback.dict())
                    is_user_query_fulfilled = feedback.isCompleted
                    should_wait = feedback.should_wait
                    yield json.dumps({"content": feedback.message, "type": "feedback"}) + "\n\n"
                    
                    if should_wait:
                        yield json.dumps({"content": "interaction_dom", "type": "context_request"}) + "\n\n"


                
                if not is_user_query_fulfilled and not should_wait:
                    yield json.dumps({"content": "interaction_dom", "type": "context_request"}) + "\n\n"
                    action_items = await generate_action_items(session_data, user_query, feedback.message)
                    # Convert ActionItem objects to dictionaries for JSON serialization
                    action_items_dict = [item.dict() for item in action_items.action_items]
                    yield json.dumps({"content": {"action_items": action_items_dict, "message": action_items.message}, "type": "action_items"}) + "\n\n"
                    if not len(action_items.action_items) > 0:
                        break
                    # assistant_message.action_items = action_items_dict
    
    #TODO: write the action items to the session_data 
    # session_data.add_event("assistant", "action_items", action_items.dict())
        
    # session_data.messages.append(assistant_message)
    session_data.save()
    
    # Stream completion
    yield json.dumps({"content": "completed", "type": "complete"}) + "\n\n"

@app.post("/api/agent-query")
def agent_query(query: AgentQuery):
    """Agent query endpoint with streaming response"""
    print(f"\n🎯 AGENT QUERY RECEIVED")
    print(f"Session: {query.session_id}")
    print(f"Question: {query.question}")
    print(f"Route: {query.current_route}")
    print("=" * 50)
    
    return StreamingResponse(
        generate_streaming_response(query), 
        media_type="text/event-stream"
    )

@app.get("/api/session-history/{session_id}")
def get_session_history(session_id: str):
    """Retrieve the complete message history for a session"""
    try:
        session_data = get_or_create_session(session_id)
        
        # Convert events to messages format for backward compatibility
        messages = []
        for event in session_data.events:
            message = Message(
                role=event["type"],
                content=event["data"],
                timestamp=datetime.fromtimestamp(event["timestamp"])
            )
            messages.append(message)
        
        return SessionHistoryResponse(
            session_id=session_id,
            messages=messages,
            context_available=bool(session_data.current_dom_summary)
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

@app.delete("/api/session/{session_id}")
def clear_session_history(session_id: str):
    """Clear message history for a session (keeps context)"""
    try:
        session_data = get_or_create_session(session_id)
        session_data.events = []  # Clear events (message history)
        session_data.save()
        return {"status": "success", "message": "Session history cleared"}
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

@app.delete("/api/session/{session_id}/complete")
def delete_session(session_id: str):
    """Delete entire session (context and messages)"""
    try:
        # Remove from memory
        remove_session_from_memory(session_id)
        
        # Delete from disk
        import os
        session_file = f"./sessions/{session_id}.json"
        if os.path.exists(session_file):
            os.remove(session_file)
        
        return {"status": "success", "message": "Session deleted"}
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")
