
"""
Company Chatbot Backend - Emily's Main Backend
FastAPI backend with TRUE MCP integration using official SDK.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json
import redis
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Import our MCP client and AI service
from mcp_client import MCPClientManager
from ai_service import AzureAIService

# Load environment variables
load_dotenv()

# ==================== LIFESPAN MANAGEMENT ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage MCP client lifecycle.
    Starts MCP server on startup, stops on shutdown.
    """
    # Startup
    print("\n" + "="*60)
    print("🚀 Company Chatbot Backend Starting...")
    print("="*60)
    
    # Start MCP client (connects to Joshna's MCP server)
    mcp_server_path = os.getenv("MCP_SERVER_PATH", "../mcp-server/mcp_server.py")
    
    try:
        import asyncio
        import traceback # Add this import at the top of your main.py file
        
        print(f"Attempting to connect to MCP Server at: {os.path.abspath(mcp_server_path)}")
        
        # Try to connect
        await MCPClientManager.get_client(mcp_server_path)
        
        print("="*60)
        print("✅ Application Ready!")
        print(f"📖 API Docs: http://localhost:8000/docs")
        print("="*60 + "\n")
        
    except Exception as e:
        # This will now print the DETAILED error from the subprocess
        print(f"❌❌❌ FAILED TO START MCP CLIENT ❌❌❌")
        print(f"The mcp_server.py script likely crashed. Here's the error it produced:")
        print(f"{e}")
        print("\n⚠️  Server starting anyway - MCP will be unavailable")
    
    yield
    
    # Shutdown
    print("\n🛑 Application shutting down...")
    await MCPClientManager.shutdown()
    print("✅ Shutdown complete\n")

# ==================== APP INITIALIZATION ====================

app = FastAPI(
    title="Company Chatbot Backend",
    description="Backend with TRUE MCP integration using official SDK",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Allow frontend to connect
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis for session storage
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

# Azure AI Service
print("🤖 Initializing AI Service...")
ai_service = AzureAIService()
print("✅ AI Service ready!")

# ==================== MODELS ====================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    tools_used: List[str] = []

# ==================== SESSION MANAGEMENT ====================

def get_session_history(session_id: str) -> List[Dict]:
    """Get conversation history from Redis."""
    data = redis_client.get(f"session:{session_id}")
    if data:
        return json.loads(data)
    return []

def save_to_history(session_id: str, role: str, content: str):
    """Save message to conversation history."""
    history = get_session_history(session_id)
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    redis_client.setex(
        f"session:{session_id}",
        86400,  # 24 hours
        json.dumps(history)
    )

# ==================== CHAT ENDPOINT ====================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with NATIVE OpenAI tool calling.
    """
    
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        print(f"\n{'='*60}")
        print(f"💬 New message: {request.message}")
        print(f"📋 Session: {session_id}")
        
        # Get MCP client
        mcp_client = await MCPClientManager.get_client(
            os.getenv("MCP_SERVER_PATH", "../mcp-server/mcp_server.py")
        )
        
        # Get available tools from MCP server
        tools = mcp_client.get_tools()
        
        print(f"🔧 Available tools: {len(tools)}")
        
        # Get conversation history
        history = get_session_history(session_id)
        
        # Build messages for AI (only user/assistant messages, no tool messages in history)
        messages = []
        for msg in history:
            # Only include user and assistant messages from history
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add new user message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Track which tools were used
        tools_used = []
        
        # Get AI response (with possible tool calls)
        ai_response = await ai_service.generate_response(messages, tools)
        
        # Handle tool calling loop
        max_iterations = 5
        iteration = 0
        
        while ai_response.get("tool_calls") and iteration < max_iterations:
            iteration += 1
            print(f"🔄 Iteration {iteration}: Processing {len(ai_response['tool_calls'])} tool call(s)")
            
            # Create assistant message with tool calls
            assistant_message = {
                "role": "assistant",
                "content": ai_response.get("content") or None  # Can be None if only tool calls
            }
            
            # Format tool calls
            tool_calls_formatted = []
            for tc in ai_response["tool_calls"]:
                tool_calls_formatted.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"])
                    }
                })
            
            assistant_message["tool_calls"] = tool_calls_formatted
            
            # DEBUG: Print the assistant message
            print(f"🔍 DEBUG: Adding assistant message:")
            print(f"   Role: {assistant_message['role']}")
            print(f"   Content: {assistant_message.get('content')}")
            print(f"   Tool calls: {len(assistant_message['tool_calls'])}")
            
            messages.append(assistant_message)
            
            # Execute tool calls and add results
            for tool_call in ai_response["tool_calls"]:
                tool_name = tool_call["name"]
                arguments = tool_call["arguments"]
                tool_call_id = tool_call["id"]
                
                tools_used.append(tool_name)
                
                # Call MCP server
                result_text = await mcp_client.call_tool(tool_name, arguments)
                
                # Create tool result message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result_text
                }
                
                # DEBUG: Print the tool message
                print(f"🔍 DEBUG: Adding tool message:")
                print(f"   Role: {tool_message['role']}")
                print(f"   Tool call ID: {tool_message['tool_call_id']}")
                print(f"   Content length: {len(tool_message['content'])}")
                
                messages.append(tool_message)
            
            # DEBUG: Print entire message history before next call
            print(f"\n🔍 DEBUG: Full message history ({len(messages)} messages):")
            for i, msg in enumerate(messages):
                print(f"   [{i}] Role: {msg['role']}, Has tool_calls: {'tool_calls' in msg}, Has tool_call_id: {'tool_call_id' in msg}")
            print()
            
            # Get next response from AI
            ai_response = await ai_service.generate_response(messages, tools)
        
        # Get final text response
        final_response = ai_response.get("content", "I apologize, but I couldn't generate a response.")
        
        print(f"✅ Final response: {final_response[:100]}...")
        print(f"🔧 Tools used: {tools_used}")
        print(f"{'='*60}\n")
        
        # Save to history (only save user message and final assistant response)
        save_to_history(session_id, "user", request.message)
        save_to_history(session_id, "assistant", final_response)
        
        return ChatResponse(
            response=final_response,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            tools_used=tools_used
        )
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== OTHER ENDPOINTS ====================

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    history = get_session_history(session_id)
    return {"history": history}

@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history."""
    redis_client.delete(f"session:{session_id}")
    return {"message": "Session cleared"}

@app.get("/api/tools")
async def list_tools():
    """Get available MCP tools."""
    try:
        mcp_client = await MCPClientManager.get_client(
            os.getenv("MCP_SERVER_PATH", "../mcp-server/mcp_server.py")
        )
        tools = mcp_client.get_tools()
        
        return {"tools": tools, "count": len(tools)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mcp_status = "unknown"
    mcp_tools_count = 0
    
    try:
        mcp_client = await MCPClientManager.get_client(
            os.getenv("MCP_SERVER_PATH", "../mcp-server/mcp_server.py")
        )
        tools = mcp_client.get_tools()
        mcp_tools_count = len(tools)
        mcp_status = "connected"
    except:
        mcp_status = "disconnected"
    
    redis_status = "connected"
    try:
        redis_client.ping()
    except:
        redis_status = "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": redis_status,
            "mcp": mcp_status,
            "mcp_tools": mcp_tools_count,
            "ai_model": ai_service.model_alias
        }
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Company Chatbot Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ==================== STARTUP ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
