"""
MCP Client - Manual JSON-RPC Implementation
Works around SDK version incompatibility issues.
"""

import asyncio
from typing import List, Dict, Any, Optional
import json
import sys
import os

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """MCP Client with manual JSON-RPC handling."""
    
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.tools: List[Dict[str, Any]] = []
        self._client_context = None
        self._read = None
        self._write = None
        self._request_id = 0
        self._pending_requests = {}
        self._reader_task = None

    async def connect(self):
        """Connect to the MCP server."""
        print(f"🚀 Connecting to MCP Server: {self.server_script_path}")
        
        if not os.path.exists(self.server_script_path):
            raise FileNotFoundError(f"MCP server script not found: {self.server_script_path}")
        
        print(f"✅ MCP server file exists")

        server_env = os.environ.copy()
        server_env["DATA_SERVER_URL"] = os.getenv("DATA_SERVER_URL", "http://localhost:5000")
        
        print(f"📡 Data Server URL: {server_env['DATA_SERVER_URL']}")

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-u", self.server_script_path],
            env=server_env
        )

        print("🔌 Creating stdio_client...")
        
        self._client_context = stdio_client(server_params)
        
        print("🔌 Entering client context...")
        
        self._read, self._write = await self._client_context.__aenter__()

        print("✅ Client context entered")
        
        # Start background reader
        self._reader_task = asyncio.create_task(self._read_responses())
        
        print("🔄 Sending initialize request...")
        
        # Send initialize request manually
        init_response = await self._send_request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "company-chatbot",
                "version": "1.0.0"
            }
        })
        
        print(f"✅ Initialize response: {init_response.get('result', {}).get('serverInfo', {}).get('name')}")
        
        print("📋 Listing tools...")
        await self._list_tools()
        print(f"✅ MCP client connected with {len(self.tools)} tools")

    async def _read_responses(self):
        """Background task to read responses from server."""
        try:
            while True:
                try:
                    # Read from the anyio stream
                    message = await asyncio.wait_for(self._read.receive(), timeout=0.1)
                    
                    # Convert SessionMessage to dict properly
                    if hasattr(message, 'message'):
                        # It's a SessionMessage wrapper
                        actual_message = message.message
                    else:
                        actual_message = message
                    
                    # Now convert the actual message to dict
                    if hasattr(actual_message, 'model_dump'):
                        msg_dict = actual_message.model_dump()
                    elif hasattr(actual_message, 'dict'):
                        msg_dict = actual_message.dict()
                    elif hasattr(actual_message, '__dict__'):
                        msg_dict = actual_message.__dict__
                    else:
                        msg_dict = actual_message
                    
                    # Debug print
                    print(f"📨 Received message type: {type(msg_dict)}, content: {msg_dict}")
                    
                    # Check if it's a response to a pending request
                    if isinstance(msg_dict, dict) and 'id' in msg_dict and msg_dict['id'] in self._pending_requests:
                        future = self._pending_requests.pop(msg_dict['id'])
                        if not future.done():
                            future.set_result(msg_dict)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"⚠️ Reader error: {e}")
                    import traceback
                    print(traceback.format_exc())
                    continue
                    
        except asyncio.CancelledError:
            pass

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request and wait for response."""
        request_id = self._request_id
        self._request_id += 1
        
        # Create future for response
        response_future = asyncio.Future()  # Changed variable name
        self._pending_requests[request_id] = response_future
        
        # Send using the format MCP SDK expects
        from mcp.types import JSONRPCMessage, JSONRPCRequest
        
        try:
            # Create proper request
            request = JSONRPCRequest(
                jsonrpc="2.0",
                id=request_id,
                method=method,
                params=params
            )
            
            # Wrap in message format that stdio_client expects
            from mcp.client.session import SessionMessage
            
            session_msg = SessionMessage(message=request)
            
            await self._write.send(session_msg)
            
        except Exception as e:
            print(f"⚠️ Send error: {e}, trying alternate format...")
            
            # Try simpler approach - send the request directly
            try:
                request = JSONRPCRequest(
                    jsonrpc="2.0",
                    id=request_id,
                    method=method,
                    params=params
                )
                await self._write.send(request)
            except Exception as e2:
                print(f"⚠️ Alternate send also failed: {e2}")
                raise
        
        # Wait for response with longer timeout
        try:
            response = await asyncio.wait_for(response_future, timeout=30.0)  # Use the correct variable name
            return response
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise RuntimeError(f"Request {method} timed out after 30 seconds")
    async def _list_tools(self):
        """Get available tools from server."""
        response = await self._send_request("tools/list", {})
        
        result = response.get('result', {})
        tools_data = result.get('tools', [])
        
        self.tools = []
        for tool in tools_data:
            # Convert from MCP Tool type to dict
            if hasattr(tool, 'model_dump'):
                tool_dict = tool.model_dump()
            elif hasattr(tool, '__dict__'):
                tool_dict = {
                    'name': tool.name,
                    'description': tool.description,
                    'input_schema': tool.inputSchema if hasattr(tool, 'inputSchema') else tool.input_schema
                }
            else:
                tool_dict = tool
            
            self.tools.append(tool_dict)

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        # Ensure all tools have input_schema key
        fixed_tools = []
        for tool in self.tools:
            fixed_tool = tool.copy()
            if 'inputSchema' in fixed_tool and 'input_schema' not in fixed_tool:
                fixed_tool['input_schema'] = fixed_tool['inputSchema']
            fixed_tools.append(fixed_tool)
        return fixed_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the server."""
        print(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}")
        
        try:
            # Increase timeout to 30 seconds
            response = await asyncio.wait_for(
                self._send_request("tools/call", {
                    "name": tool_name,
                    "arguments": arguments
                }),
                timeout=30.0  # Changed from 10 to 30
            )
            
            result = response.get('result', {})
            content = result.get('content', [])
            
            # Extract text from content
            text_parts = []
            for item in content:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
            
            result_text = "\n".join(text_parts) if text_parts else "No result"
            
            print(f"✅ Tool result received ({len(result_text)} chars)")
            return result_text
            
        except asyncio.TimeoutError:
            error_msg = f"Tool {tool_name} timed out after 30 seconds"
            print(f"❌ {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Error calling tool {tool_name}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    async def disconnect(self):
        """Disconnect from server."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        
        if self._client_context:
            await self._client_context.__aexit__(None, None, None)
        
        print("🛑 MCP client disconnected")


class MCPClientManager:
    """Singleton manager for MCP client."""
    _instance: Optional[MCPClient] = None

    @classmethod
    async def get_client(cls, server_path: str) -> MCPClient:
        if cls._instance is None:
            cls._instance = MCPClient(server_path)
            await cls._instance.connect()
        return cls._instance
    
    @classmethod
    async def shutdown(cls):
        if cls._instance:
            await cls._instance.disconnect()
            cls._instance = None
