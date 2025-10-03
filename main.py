from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents.action_items_extractor_agent import action_items_extractor_agent
from agents.webassistant import web_assistant_agent
from fastapi.responses import StreamingResponse
from tools import query_document, read_file
from dotenv import load_dotenv
from datetime import datetime
import json

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

class SessionData(BaseModel):
    context: Dict[str, Any]
    messages: List[Message] = []

class ContextPayload(BaseModel):
    distilledNodes: Optional[list]
    mainTree: Optional[list]
    appState: Optional[dict]

class AgentQuery(BaseModel):
    session_id: str
    question: str

class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[Message]
    context_available: bool

# Store session data with both context and message history
user_sessions: Dict[str, SessionData] = {}

@app.post("/api/update-context")
async def update_context(context: ContextPayload, x_session_id: Optional[str] = Header(None)):
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header")
    
    # Initialize or update session data
    if x_session_id not in user_sessions:
        user_sessions[x_session_id] = SessionData(context=context.dict(), messages=[])
    else:
        user_sessions[x_session_id].context = context.dict()
    
    return {"status": "success"}

def generate_streaming_response(query: AgentQuery):
    """Generator function for streaming responses"""
    session_data = user_sessions.get(query.session_id)
    if not session_data:
        yield json.dumps({"error": "No session found", "type": "error"}) + "\n\n"
        return
    
    context = session_data.context
    if not context:
        yield json.dumps({"error": "No context found for session", "type": "error"}) + "\n\n"
        return

    yield json.dumps({"content": "Processing query", "type": "point"}) + "\n\n"
    
    # Add user message to session history
    user_message = Message(
        role="user",
        content=query.question,
        timestamp=datetime.now()
    )
    session_data.messages.append(user_message)
    
    # Get conversation history for the agent
    conversation_history = session_data.messages
    
    # Get response from web assistant agent
    answer = web_assistant_agent(context, query.question, conversation_history)
    
    # Add assistant response to session history
    assistant_message = Message(
        role="assistant",
        content=answer.answer,
        timestamp=datetime.now()
    )
    
    # Stream the answer
    yield json.dumps({"content": answer.answer, "type": "answer"}) + "\n\n"
    
    action_items = None
    if answer.need_to_perform_action_items:
        action_items = action_items_extractor_agent(context, query.question)
        # Convert ActionItem objects to dictionaries for JSON serialization
        action_items_dict = [item.dict() for item in action_items.action_items]
        assistant_message.action_items = action_items_dict
        yield json.dumps({"content": action_items_dict, "type": "action_items"}) + "\n\n"
    
    session_data.messages.append(assistant_message)
    
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
    session_data = user_sessions.get(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionHistoryResponse(
        session_id=session_id,
        messages=session_data.messages,
        context_available=bool(session_data.context)
    )

@app.delete("/api/session/{session_id}")
def clear_session_history(session_id: str):
    """Clear message history for a session (keeps context)"""
    session_data = user_sessions.get(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data.messages = []
    return {"status": "success", "message": "Session history cleared"}

@app.delete("/api/session/{session_id}/complete")
def delete_session(session_id: str):
    """Delete entire session (context and messages)"""
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del user_sessions[session_id]
    return {"status": "success", "message": "Session deleted"}
