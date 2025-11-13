#!/usr/bin/env python3
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Try importing InitializationOptions
try:
    from mcp.server.models import InitializationOptions
    HAS_INIT_OPTIONS = True
except ImportError:
    HAS_INIT_OPTIONS = False

try:
    from mcp.server import NotificationOptions
    HAS_NOTIFICATION_OPTIONS = True
except ImportError:
    HAS_NOTIFICATION_OPTIONS = False

server = Server("test-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="test_tool",
            description="A test tool",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    return [TextContent(type="text", text="Hello from test tool!")]

async def main():
    import sys
    # Force UTF-8 output
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    print("Starting Test MCP Server...", file=sys.stderr, flush=True)
    print(f"Has InitializationOptions: {HAS_INIT_OPTIONS}", file=sys.stderr, flush=True)
    print(f"Has NotificationOptions: {HAS_NOTIFICATION_OPTIONS}", file=sys.stderr, flush=True)
    
    async with stdio_server() as streams:
        print(f"stdio_server returned {len(streams)} streams", file=sys.stderr, flush=True)
        
        if len(streams) == 2:
            read_stream, write_stream = streams
        else:
            print(f"ERROR: Unexpected number of streams: {streams}", file=sys.stderr, flush=True)
            return
        
        print("Streams extracted, calling server.run()", file=sys.stderr, flush=True)
        
        # Try different run() signatures
        try:
            if HAS_INIT_OPTIONS and HAS_NOTIFICATION_OPTIONS:
                print("Trying: server.run() with InitializationOptions", file=sys.stderr, flush=True)
                await server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="test-server",
                        server_version="1.0.0",
                        capabilities=server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
            else:
                print("Trying: server.run() without InitializationOptions", file=sys.stderr, flush=True)
                await server.run(read_stream, write_stream)
        except TypeError as e:
            print(f"TypeError in server.run(): {e}", file=sys.stderr, flush=True)
            
            # Try with just streams
            print("Trying: server.run() with just 2 args", file=sys.stderr, flush=True)
            await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
