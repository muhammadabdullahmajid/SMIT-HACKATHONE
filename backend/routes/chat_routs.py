from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId
from config.database import get_db
from student_agent.agent_help import triage_agent
from agents import Runner
from utils.auth_utils import get_current_user
import json
import asyncio

load_dotenv()

db = get_db()
chats_collection = db["chats"]
threads_collection = db["threads"]

chat = APIRouter()

class ChatRequest(BaseModel):
    user_input: str
    thread_id: Optional[str] = None  # Optional thread_id for continuing existing conversations
    stream: Optional[bool] = False  # Whether to stream the response

def save_message(user_id: str, thread_id: str, role: str, content: str):
    chat_doc = {
        "user_id": user_id,
        "thread_id": thread_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    }
    result = chats_collection.insert_one(chat_doc)
    return str(result.inserted_id)

def create_new_thread(user_id: str) -> str:
    """
    🔑 Create a brand new thread for each chat session.
    """
    result = threads_collection.insert_one({
        "user_id": user_id,
        "title": "New Conversation",
        "created_at": datetime.utcnow()
    })
    return str(result.inserted_id)

@chat.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Streaming chat endpoint"""
    try:
        print(f"Received streaming request: {request}")
        print(f"Request user_input: {request.user_input}")
        print(f"Request thread_id: {request.thread_id}")
        
        user_id = str(current_user["user_id"])
        user_text = request.user_input.strip()
        if not user_text:
            raise HTTPException(status_code=400, detail="User input cannot be empty.")

        # ✅ Create new thread for each chat session or use provided thread_id
        if request.thread_id and not request.thread_id.startswith("temp-"):
            # Use existing thread if provided and not a temporary ID
            thread_id = request.thread_id
            # Verify thread belongs to user
            thread = threads_collection.find_one({"_id": ObjectId(thread_id), "user_id": user_id})
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found or access denied")
        else:
            # Create new thread for new chat session
            thread_id = create_new_thread(user_id)

        # Save user message
        save_message(user_id, thread_id, "user", user_text)

        # Update thread title with first message if it's a new thread
        if not request.thread_id or request.thread_id.startswith("temp-"):
            # This is a new thread, update the title with the first message
            thread_title = user_text[:50] + "..." if len(user_text) > 50 else user_text
            threads_collection.update_one(
                {"_id": ObjectId(thread_id)},
                {"$set": {"title": thread_title}}
            )

        # Fetch latest 10 messages for context
        history_cursor = chats_collection.find(
            {"user_id": user_id, "thread_id": thread_id}
        ).sort("timestamp", -1).limit(10)
        history = list(history_cursor)[::-1]

        messages = [{"role": doc["role"], "content": doc["content"]} for doc in history]

        async def generate_stream():
            try:
                # Send initial metadata
                yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id})}\n\n"
                
                # Stream the AI response
                result = Runner.run_streamed(triage_agent, messages)
                full_response = ""
                
                async for event in result.stream_events():
                    # Debug: print all events to see what we're getting
                    print(f"Streaming event: {event.type} - {event}")
                    
                    # Handle specific event types based on the actual structure
                    if event.type == "raw_response_event":
                        # Check if this is a ResponseTextDeltaEvent
                        if hasattr(event, 'data') and hasattr(event.data, 'delta'):
                            delta = event.data.delta
                            print(f"Found delta in raw_response_event: '{delta}'")
                            if delta:  # Only send non-empty deltas
                                full_response += delta
                                print(f"Sending delta: '{delta}'")
                                yield f"data: {json.dumps({'type': 'delta', 'content': delta})}\n\n"
                    
                    elif event.type == "response.content_part.done":
                        # This event contains the complete text content
                        if hasattr(event, 'part') and hasattr(event.part, 'text'):
                            text = event.part.text
                            print(f"Found text in content_part.done: '{text}'")
                            if text:  # Only send non-empty text
                                full_response += text
                                print(f"Sending delta: '{text}'")
                                yield f"data: {json.dumps({'type': 'delta', 'content': text})}\n\n"
                
                # Save the complete assistant reply
                save_message(user_id, thread_id, "assistant", full_response)
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"
                
            except Exception as e:
                print(f"Error in streaming: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )

    except Exception as e:
        print("Error in streaming chat endpoint:", str(e))
        error_detail = str(e) if e else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=error_detail)

@chat.post("/")
async def chat_endpoint(
    request: ChatRequest = Body(...),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    try:
        print(f"Received request: {request}")
        print(f"Request user_input: {request.user_input}")
        print(f"Request thread_id: {request.thread_id}")
        
        user_id = str(current_user["user_id"])
        user_text = request.user_input.strip()
        if not user_text:
            raise HTTPException(status_code=400, detail="User input cannot be empty.")

        # ✅ Create new thread for each chat session or use provided thread_id
        if request.thread_id and not request.thread_id.startswith("temp-"):
            # Use existing thread if provided and not a temporary ID
            thread_id = request.thread_id
            # Verify thread belongs to user
            thread = threads_collection.find_one({"_id": ObjectId(thread_id), "user_id": user_id})
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found or access denied")
        else:
            # Create new thread for new chat session
            thread_id = create_new_thread(user_id)

        # Save user message
        save_message(user_id, thread_id, "user", user_text)

        # Update thread title with first message if it's a new thread
        if not request.thread_id or request.thread_id.startswith("temp-"):
            # This is a new thread, update the title with the first message
            thread_title = user_text[:50] + "..." if len(user_text) > 50 else user_text
            threads_collection.update_one(
                {"_id": ObjectId(thread_id)},
                {"$set": {"title": thread_title}}
            )

        # Fetch latest 10 messages for context
        history_cursor = chats_collection.find(
            {"user_id": user_id, "thread_id": thread_id}
        ).sort("timestamp", -1).limit(10)
        history = list(history_cursor)[::-1]

        messages = [{"role": doc["role"], "content": doc["content"]} for doc in history]

        # AI agent response
        result = await Runner.run(triage_agent, messages)
        print(f"Agent result type: {type(result)}")
        print(f"Agent result: {result}")
        
        # Handle different possible result structures
        if hasattr(result, 'final_output'):
            assistant_reply = result.final_output
        elif hasattr(result, 'content'):
            assistant_reply = result.content
        elif isinstance(result, str):
            assistant_reply = result
        else:
            assistant_reply = str(result) if result else "I'm sorry, I couldn't generate a response."

        # Save assistant reply
        save_message(user_id, thread_id, "assistant", assistant_reply)

        # Return full thread history
        full_history_cursor = chats_collection.find(
            {"user_id": user_id, "thread_id": thread_id}
        ).sort("timestamp", 1)
        full_history = [
            {
                "id": str(doc["_id"]),
                "thread_id": doc["thread_id"],
                "role": doc["role"],
                "content": doc["content"],
                "timestamp": doc["timestamp"]
            }
            for doc in full_history_cursor
        ]

        return {
            "user_id": user_id,
            "thread_id": thread_id,
            "response": assistant_reply,
            "history": full_history
        }

    except Exception as e:
        print("Error in chat endpoint:", str(e))
        error_detail = str(e) if e else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=error_detail)

@chat.get("/threads")
async def get_threads(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["user_id"])
    threads = list(threads_collection.find({"user_id": user_id}).sort("created_at", -1))
    for t in threads:
        t["id"] = str(t["_id"])
        del t["_id"]
    return {"threads": threads}

@chat.post("/threads/new")
async def create_new_thread_endpoint(current_user: dict = Depends(get_current_user)):
    """Create a new thread for the current user"""
    user_id = str(current_user["user_id"])
    thread_id = create_new_thread(user_id)
    return {"thread_id": thread_id, "message": "New thread created successfully"}

@chat.get("/threads/{thread_id}")
async def get_thread_messages(thread_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["user_id"])
    thread = threads_collection.find_one({"_id": ObjectId(thread_id), "user_id": user_id})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    messages = list(chats_collection.find({"thread_id": thread_id}).sort("timestamp", 1))
    for m in messages:
        m["id"] = str(m["_id"])
        del m["_id"]
    return {"thread_id": thread_id, "messages": messages}
