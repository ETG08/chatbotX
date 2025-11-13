import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters

async def run_test():
    """A minimal test to check if capture_stderr is supported."""
    
    print("--- STARTING MCP LIBRARY TEST ---")
    
    # Path to Joshna's server (must exist for the test to run)
    server_script_path = "../mcp-server/mcp_server.py"

    server_params = StdioServerParameters(
        command="python",
        args=["-u", server_script_path],
    )

    try:
        print("Attempting to call stdio_client() with 'capture_stderr=True'...")
        
        # This is the line that is failing in your main code
        client_context = stdio_client(
            server_params,
            capture_stderr=True 
        )
        
        print("✅ SUCCESS! Your 'mcp' library supports 'capture_stderr'.")
        print("The problem is likely a caching issue with your main app.")
        
        # We don't need to actually connect, just check if the call works
        # This part will likely not be reached if the library is old.
        
    except TypeError as e:
        print("\n❌❌❌ TEST FAILED! ❌❌❌")
        print("This confirms the error is with the 'mcp' library itself.")
        print(f"Error Message: {e}")
        print("\nThis means your installed version of the 'mcp' package is too old.")
        print("Please proceed to the 'SOLUTION' steps to fix this.")
        
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

    print("\n--- MCP LIBRARY TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(run_test())
