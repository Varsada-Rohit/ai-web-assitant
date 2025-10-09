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

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    content = read_file(file)
    return {"filename": file.filename, "content": content}

@app.post("/query")
def query_document_api(query: str):
    return {"query": query, "result": query_document(query)}

# @app.post("/upload-pymupdf")
# def upload_file(file: UploadFile = File(...)):
#     print("FILE LOG",file)
#     content = read_file_using_pymupdf_langchain(file)
#     return {"filename": file.filename, "content": content}




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
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header")

    context_summary = summarise_agent(context.dict())

    session = get_or_create_session(x_session_id)
    session.update_current_dom_summary(context_summary.summary)
    session.save()
    
    return {"status": "success"}

@app.post("/api/update-interaction-dom")
async def update_interaction_dom(interaction_dom: ContextPayload, x_session_id: Optional[str] = Header(None)):

    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header")
    
    session = get_or_create_session(x_session_id)
    session.update_current_interaction_dom(interaction_dom.dict())
    if x_session_id in session_event_locks:
        session_event_locks[x_session_id].set()
    session.save()    
    return {"status": "success"}

async def generate_action_items(session_data: Session, query: str, feedback: Optional[str] = None) -> ActionItemsExtractorResponse:
    print('WAITING FOR RESUME EVENT')
    if session_data.session_id not in session_event_locks:
        session_event_locks[session_data.session_id] = asyncio.Event()
    await session_event_locks[session_data.session_id].wait()
    session_event_locks[session_data.session_id].clear()
    print('RESUME EVENT SET')
    context = session_data.current_interaction_dom
    session_data.current_interaction_dom = None

    action_items = action_items_extractor_agent(context, query,session_data.get_recent_context(),feedback)

    session_data.add_event("assistant", "action_planner_agent", action_items.dict())
    
    
    
    return action_items

async def generate_streaming_response(query: AgentQuery):
    """Generator function for streaming responses"""

    if not Session.session_exists(query.session_id):
        yield json.dumps({"error": "No session found", "type": "error"}) + "\n\n"
        return

    # Check if session exists and get or create it
    session_data = get_or_create_session(query.session_id)
    
    context_summary = session_data.current_dom_summary
    if not context_summary:
        yield json.dumps({"error": "No context found for session", "type": "error"}) + "\n\n"
        return

    yield json.dumps({"content": "Processing query", "type": "point"}) + "\n\n"
    
    session_data.add_event("user", "client", query.question)
    
    # Get conversation history for the agent
    conversation_history = session_data.get_recent_context()

    # Get response from web assistant agent
    answer = web_assistant_agent(context_summary, query.question, conversation_history)

    user_query = query.question
    
    
    session_data.add_event("assistant", "general_agent", answer.answer)

    # •	context_dom
	# •	interaction_dom
    
    # Stream the answer
    yield json.dumps({"content": answer.answer, "type": "answer"}) + "\n\n"

    print("answer",answer)
    
    action_items = None
    if answer.need_to_perform_action_items:
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
                    print("feedback",feedback)
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
    

        
    
    # session_data.messages.append(assistant_message)
    session_data.save()
    
    # Stream completion
    yield json.dumps({"content": "completed", "type": "complete"}) + "\n\n"

@app.post("/api/agent-query")
def agent_query(query: AgentQuery):
    """Agent query endpoint with streaming response"""
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
