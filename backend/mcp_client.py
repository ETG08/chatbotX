"""
MCP Client - FastMCP Version
Much simpler implementation using FastMCP's built-in client.
"""

import asyncio
from typing import List, Dict, Any, Optional
import sys
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Simplified MCP Client using FastMCP server."""
    
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.tools: List[Dict[str, Any]] = []
        self._exit_stack = None

    async def connect(self):
        """Connect to the FastMCP server."""
        print(f"🚀 Connecting to FastMCP Server: {self.server_script_path}")
        
        if not os.path.exists(self.server_script_path):
            raise FileNotFoundError(f"MCP server script not found: {self.server_script_path}")
        
        server_env = os.environ.copy()
        server_env["DATA_SERVER_URL"] = os.getenv("DATA_SERVER_URL", "http://localhost:5000")
        
        print(f"📡 Data Server URL: {server_env['DATA_SERVER_URL']}")

        # Create server parameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script_path],
            env=server_env
        )

        print("🔌 Creating stdio_client...")
        
        # Connect using stdio_client
        from contextlib import AsyncExitStack
        
        self._exit_stack = AsyncExitStack()
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        
        stdio, write = stdio_transport
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )
        
        # Initialize the session
        await self.session.initialize()
        
        print("✅ Session initialized")
        
        # List available tools
        await self._list_tools()
        
        print(f"✅ MCP client connected with {len(self.tools)} tools")

    async def _list_tools(self):
        """Get available tools from server."""
        response = await self.session.list_tools()
        
        self.tools = []
        for tool in response.tools:
            tool_dict = {
                'name': tool.name,
                'description': tool.description,
                'input_schema': tool.inputSchema
            }
            self.tools.append(tool_dict)

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools in OpenAI format."""
        return self.tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the server."""
        print(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract text from result
            text_parts = []
            for content in result.content:
                if hasattr(content, 'text'):
                    text_parts.append(content.text)
            
            result_text = "\n".join(text_parts) if text_parts else "No result"
            
            print(f"✅ Tool result received ({len(result_text)} chars)")
            return result_text
            
        except Exception as e:
            error_msg = f"Error calling tool {tool_name}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    async def disconnect(self):
        """Disconnect from server."""
        if self._exit_stack:
            await self._exit_stack.aclose()
        
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
