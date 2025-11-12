"""
MCP Client - Using Official MCP SDK
Communicates with MCP Server using the standard MCP client libraries.
"""

import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

# Official MCP Client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

class MCPClient:
    """
    MCP Client using official SDK.
    Manages connection to MCP server.
    """
    def __init__(self, server_script_path: str):
        """
        Initialize MCP Client.
        
        Args:
            server_script_path: Path to MCP server script
        """
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self._client_context = None
        self._read = None
        self._write = None

    async def connect(self):
        """Connect to the MCP server."""
        print(f"Connecting to MCP Server: {self.server_script_path}")

        # Configure server parameters
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script_path],
            env=None # Can pass environment variables here if needed
        )

        # Create stdio client context
        self._client_context = stdio_client(server_params)
        self._read, self._write = await self._client_context.__aenter__()

        # Create Session
        self.session = ClientSession(self._read, self._write)

        # Initialize the session
        await self.session.initialize()

        print("✅ MCP session initialized")

        # List available tools
        await self._list_tools()

        print(f"✅ MCP client connected with {len(self.tools)} tools")

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self._client_context:
            await self._client_context.__aexit__(None, None, None)
        print("🛑 MCP client disconnected")

    async def _list_tools(self):
        """Get list of available tools from MCP server."""
        if not self.session:
            raise RuntimeError("MCP session not initialized")
        # Request tools list
        response = await self.session.list_tools()
        
        self.tools = response.tools
        
        print(f"📋 Available tools:")
        for tool in self.tools:
            print(f"   - {tool.name}: {tool.description[:60]}...")

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools in dictionary format.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in self.tools
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool result as string
        """

        if not self.session:
            raise  RuntimeError("MCP session not initialized")
        
        print(f"🔧 Calling MCP tool: {tool_name}")
        print(f"📥 Arguments: {arguments}")

        try:
            # Call the tool
            result = await self.session.call_tool(tool_name, arguments)

            # Extract text content from result
            if result.content:
                # MCP returns a list of content blocks
                text_parts = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        text_parts.append(content.text)

                result_text = "\n".join(text_parts)

                print(f"✅ Tool result received ({len(result_text)} chars)")

                return result_text
            else:
                print("⚠️ Tool returned empty result")
                return "No result returned"
            
        except Exception as e:
            error_msg = f"Error calling tool {tool_name}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
        
class MCPClientManager:
    """
    Manages MCP client lifecycle.
    Singleton pattern to ensure only one MCP client exists.
    """
    _instance: Optional[MCPClient] = None

    @classmethod
    async def get_client(cls, server_path: str) -> MCPClient:
        """
        Get or create MCP client instance.
        
        Args:
            server_path: Path to MCP server script
            
        Returns:
            Connected MCP client
        """
        if cls._instance is None:
            cls._instance = MCPClient(server_path)
            await cls._instance.connect()
        return cls._instance
    
    @classmethod
    async def shutdown(cls):
        """Shutdown MCP client."""
        if cls._instance:
            await cls._instance.disconnect()
            cls._instance = None

# Context manager helper
@asynccontextmanager
async def get_mcp_client(server_path: str):
    """
    Context manager for MCP client.
    
    Usage:
        async with get_mcp_client("/path/to/server.py") as client:
            tools = client.get_tools()
            result = await client.call_tool("search_employees", {"search": "John"})
    """
    client = MCPClient(server_path)
    await client.connect()

    try:
        yield client
    finally:
        await client.disconnect()