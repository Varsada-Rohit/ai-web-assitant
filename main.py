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
    session_data.save()
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

    # ========================================
    # PLAN-BASED EXECUTION LOOP
    # ========================================

    print("\n🔄 STARTING PLAN-BASED EXECUTION LOOP")

    # Initialize execution state
    execution_state = {
        "completed_steps": [],
        "current_batch_steps": [],
        "remaining_steps": list(range(1, action_plan.total_steps + 1)),
        "current_iteration": 0,
        "task_completed": False
    }

    print(f"📊 Initial Execution State:")
    print(f"   Total Steps: {action_plan.total_steps}")
    print(f"   Remaining Steps: {execution_state['remaining_steps']}")

    # Import action items extractor
    from agents.action_items_extractor_agent import action_items_extractor_agent

    # Execution loop - continue until task is completed
    while not execution_state["task_completed"]:
        execution_state["current_iteration"] += 1

        print(f"\n{'='*60}")
        print(f"🔄 ITERATION {execution_state['current_iteration']}")
        print(f"{'='*60}")
        print(f"📊 Execution State:")
        print(f"   Completed: {execution_state['completed_steps']}")
        print(f"   Remaining: {execution_state['remaining_steps']}")

        # Get DOM for this iteration
        # - Iteration 1: Uses DOM fetched before action planning (lines 208-215)
        # - Iteration 2+: Wait for FE to send updated DOM via update_interaction_dom after executing actions
        if execution_state["current_iteration"] == 1:
            print(f"📋 Using initial DOM from session (iteration 1)")
            current_dom = session_data.current_interaction_dom
        else:
            print(f"⏳ Waiting for updated DOM from frontend (iteration {execution_state['current_iteration']})...")
            # Wait for FE to send updated DOM via update_interaction_dom endpoint
            if session_data.session_id not in session_event_locks:
                session_event_locks[session_data.session_id] = asyncio.Event()
            await session_event_locks[session_data.session_id].wait()
            session_event_locks[session_data.session_id].clear()
            print("✅ Updated DOM received from frontend")
            current_dom = session_data.current_interaction_dom

        session_data.current_interaction_dom = None

        # Generate batched actions for next executable step(s)
        print(f"🤖 Calling Action Items Extractor Agent...")
        action_items_response = action_items_extractor_agent(
            context=current_dom,
            query=query.question,
            action_plan=action_plan.dict(),
            execution_state=execution_state,
            conversation_history=conversation_history
        )

        # Update execution state from response
        execution_state["completed_steps"] = action_items_response.completed_steps
        execution_state["current_batch_steps"] = action_items_response.current_batch_steps
        execution_state["remaining_steps"] = action_items_response.remaining_steps
        execution_state["task_completed"] = action_items_response.task_completed

        # Log progress
        print(f"\n📊 EXECUTION PROGRESS - Iteration {execution_state['current_iteration']}")
        print(f"   Completed Steps: {action_items_response.completed_steps}")
        print(f"   Current Batch: {action_items_response.current_batch_steps}")
        print(f"   Remaining Steps: {action_items_response.remaining_steps}")
        print(f"   Batch Reason: {action_items_response.batch_reason}")
        if action_items_response.blocked_reason:
            print(f"   ⚠️  Blocked Reason: {action_items_response.blocked_reason}")
        print(f"   Task Completed: {action_items_response.task_completed}")

        # Log event to session (including actual action items)
        session_data.add_event("assistant", "action_items_extractor", {
            "iteration": execution_state["current_iteration"],
            "completed_steps": action_items_response.completed_steps,
            "current_batch_steps": action_items_response.current_batch_steps,
            "remaining_steps": action_items_response.remaining_steps,
            "task_completed": action_items_response.task_completed,
            "batch_reason": action_items_response.batch_reason,
            "blocked_reason": action_items_response.blocked_reason,
            "action_items_count": len(action_items_response.action_items),
            "action_items": [item.dict() for item in action_items_response.action_items],  # Full action items with selectors
            "message": action_items_response.message
        })
        session_data.save()

        # Stream actions and progress to frontend
        action_items_dict = [item.dict() for item in action_items_response.action_items]
        yield json.dumps({
            "content": {
                "action_items": action_items_dict,
                "message": action_items_response.message,
                "progress": {
                    "completed_steps": action_items_response.completed_steps,
                    "current_batch_steps": action_items_response.current_batch_steps,
                    "remaining_steps": action_items_response.remaining_steps,
                    "batch_reason": action_items_response.batch_reason,
                    "blocked_reason": action_items_response.blocked_reason,
                    "iteration": execution_state["current_iteration"],
                    "task_completed": action_items_response.task_completed
                }
            },
            "type": "action_items"
        }) + "\n\n"

        # Check if no actions were generated (blocked or error state)
        if len(action_items_response.action_items) == 0:
            if action_items_response.task_completed:
                print("✅ Task completed with no remaining actions")
                break
            elif action_items_response.blocked_reason:
                print(f"⚠️  Execution blocked: {action_items_response.blocked_reason}")
                yield json.dumps({
                    "content": f"⚠️ Execution blocked: {action_items_response.blocked_reason}",
                    "type": "error"
                }) + "\n\n"
                break
            else:
                print("⚠️  No actions generated but task not complete - possible error")
                break

        # If task marked as completed, exit loop
        if action_items_response.task_completed:
            print(f"\n✅ TASK COMPLETED!")
            print(f"   Total Iterations: {execution_state['current_iteration']}")
            print(f"   All {action_plan.total_steps} steps executed successfully")

            yield json.dumps({
                "content": f"✅ Task completed! All {action_plan.total_steps} steps executed successfully in {execution_state['current_iteration']} iteration(s).",
                "type": "completion"
            }) + "\n\n"
            break

        # Safety check: prevent infinite loops (max 10 iterations)
        if execution_state["current_iteration"] >= 10:
            print("⚠️  Maximum iterations reached (10) - stopping execution")
            yield json.dumps({
                "content": "⚠️ Maximum iterations reached. Task may not be complete.",
                "type": "warning"
            }) + "\n\n"
            break

    print(f"\n{'='*60}")
    print(f"🏁 EXECUTION LOOP COMPLETED")
    print(f"{'='*60}")
    print(f"   Total Iterations: {execution_state['current_iteration']}")
    print(f"   Final Completed Steps: {execution_state['completed_steps']}")
    print(f"   Task Completed: {execution_state['task_completed']}")
    print(f"{'='*60}\n")
        
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
