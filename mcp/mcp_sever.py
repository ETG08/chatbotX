#!/usr/bin/env python3
"""
MCP Server that retrieves data from local data server.
Replaces Zoho People API integration.
"""

import asyncio
from typing import Any
import requests

# ✅ Real MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Local data server URL
DATA_SERVER_URL = "http://localhost:5000"

# ✅ Create MCP Server
server = Server("company-data-server")

# ==================== MCP TOOL DEFINITIONS ====================

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Define available tools."""
    return [
        Tool(
            name="search_employees",
            description="Search for employees by name, email, or ID. You can also filter by department.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term (name, email, or ID)"
                    },
                    "department": {
                        "type": "string",
                        "description": "Filter by department (optional)"
                    }
                }
            }
        ),

        Tool(
            name="get_employee_by_id",
            description="Get detailed information about a specific employee by their ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID (e.g., EMP001)"
                    }
                },
                "required": ["employee_id"]
            }
        ),

        Tool(
            name="get_leave_balance",
            description="Get leave balance for a specific employee.",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID"
                    }
                },
                "required": ["employee_id"]
            }
        ),

        Tool(
            name="get_departments",
            description="Get list of all departments in the company.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        Tool(
            name="get_holidays",
            description="Get list of company holidays.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        Tool(
            name="get_announcements",
            description="Get recent company announcements.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Number of announcements to retrieve (default: 5)",
                        "default": 5
                    }
                }
            }
        ),

        Tool(
            name="search_policies",
            description="Search company policies by keyword.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term (e.g., 'remote work', 'leave')"
                    }
                }
            }
        )
    ]

# ==================== MCP TOOL HANDLERS ====================

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool execution."""

    print(f"🔧 Tool called: {name}", flush=True)
    print(f"📥 Arguments: {arguments}", flush=True)

    try:
        if name == "search_employees":
            return await handle_search_employees(arguments)

        elif name == "get_employee_by_id":
            return await handle_get_employee_by_id(arguments)

        elif name == "get_leave_balance":
            return await handle_get_leave_balance(arguments)

        elif name == "get_departments":
            return await handle_get_departments()

        elif name == "get_holidays":
            return await handle_get_holidays()

        elif name == "get_announcements":
            return await handle_get_announcements(arguments)

        elif name == "search_policies":
            return await handle_search_policies(arguments)

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        print(f"❌ Error: {str(e)}", flush=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# ==================== INDIVIDUAL HANDLERS ====================

async def handle_search_employees(arguments: dict) -> list[TextContent]:
    """Search employees."""
    params = {}
    if arguments.get("search"):
        params["search"] = arguments["search"]
    if arguments.get("department"):
        params["department"] = arguments["department"]

    response = requests.get(f"{DATA_SERVER_URL}/api/employees", params=params)
    response.raise_for_status()
    data = response.json()

    if not data.get('data'):
        return [TextContent(type="text", text="No employees found")]

    employees = data['data']
    result = f"## Found {len(employees)} employee(s):\n\n"

    for emp in employees:
        result += f"### {emp['firstName']} {emp['lastName']}\n"
        result += f"- **ID:** {emp['id']}\n"
        result += f"- **Email:** {emp['email']}\n"
        result += f"- **Department:** {emp['department']}\n"
        result += f"- **Designation:** {emp['designation']}\n\n"

    return [TextContent(type="text", text=result)]

async def handle_get_employee_by_id(arguments: dict) -> list[TextContent]:
    """Get employee by ID."""
    employee_id = arguments["employee_id"]

    response = requests.get(f"{DATA_SERVER_URL}/api/employees/{employee_id}")

    if response.status_code == 404:
        return [TextContent(type="text", text=f"Employee {employee_id} not found")]

    response.raise_for_status()
    data = response.json()

    emp = data['data'][0]

    result = f"## {emp['firstName']} {emp['lastName']}\n\n"
    result += "### Basic Information\n"
    result += f"- **ID:** {emp['id']}\n"
    result += f"- **Email:** {emp['email']}\n"
    result += f"- **Phone:** {emp['phone']}\n\n"
    result += "### Employment Details\n"
    result += f"- **Department:** {emp['department']}\n"
    result += f"- **Designation:** {emp['designation']}\n"
    result += f"- **Manager:** {emp['manager']}\n"
    result += f"- **Joined:** {emp['dateOfJoining']}\n"
    result += f"- **Location:** {emp['location']}\n"
    result += f"- **Status:** {emp['status']}\n"

    return [TextContent(type="text", text=result)]

async def handle_get_leave_balance(arguments: dict) -> list[TextContent]:
    """Get leave balance."""
    employee_id = arguments["employee_id"]

    response = requests.get(f"{DATA_SERVER_URL}/api/leave/{employee_id}")

    if response.status_code == 404:
        return [TextContent(type="text", text=f"Leave balance not found for {employee_id}")]

    response.raise_for_status()
    data = response.json()

    result = f"## Leave Balance for {employee_id}\n\n"

    for leave in data['data']:
        result += f"### {leave['leaveType']}\n"
        result += f"- **Total:** {leave['total']} days\n"
        result += f"- **Used:** {leave['used']} days\n"
        result += f"- **Available:** {leave['available']} days\n\n"

    return [TextContent(type="text", text=result)]

async def handle_get_departments() -> list[TextContent]:
    """Get departments."""
    response = requests.get(f"{DATA_SERVER_URL}/api/departments")
    response.raise_for_status()
    data = response.json()

    result = "## Company Departments\n\n"

    for dept in data['data']:
        result += f"### {dept['name']}\n"
        result += f"- **Description:** {dept['description']}\n"
        result += f"- **Head Count:** {dept['headCount']}\n"
        result += f"- **Manager:** {dept['manager']}\n\n"

    return [TextContent(type="text", text=result)]

async def handle_get_holidays() -> list[TextContent]:
    """Get holidays."""
    response = requests.get(f"{DATA_SERVER_URL}/api/holidays")
    response.raise_for_status()
    data = response.json()

    result = "## Company Holidays\n\n"

    for holiday in data['data']:
        result += f"### {holiday['name']}\n"
        result += f"- **Date:** {holiday['date']}\n"
        result += f"- **Type:** {holiday['type']}\n\n"

    return [TextContent(type="text", text=result)]

async def handle_get_announcements(arguments: dict) -> list[TextContent]:
    """Get announcements."""
    limit = arguments.get("limit", 5)

    response = requests.get(f"{DATA_SERVER_URL}/api/announcements", params={"limit": limit})
    response.raise_for_status()
    data = response.json()

    result = "## Recent Announcements\n\n"

    for ann in data['data']:
        result += f"### {ann['title']}\n"
        result += f"- **Date:** {ann['date']}\n"
        result += f"- **Author:** {ann['author']}\n"
        result += f"\n{ann['content']}\n\n---\n\n"

    return [TextContent(type="text", text=result)]

async def handle_search_policies(arguments: dict) -> list[TextContent]:
    """Search policies."""
    params = {}
    if arguments.get("search"):
        params["search"] = arguments["search"]

    response = requests.get(f"{DATA_SERVER_URL}/api/policies", params=params)
    response.raise_for_status()
    data = response.json()

    if not data.get('data'):
        return [TextContent(type="text", text="No policies found")]

    result = "## Company Policies\n\n"

    for policy in data['data']:
        result += f"### {policy['title']}\n"
        result += f"- **Category:** {policy['category']}\n"
        result += f"\n{policy['content']}\n\n---\n\n"

    return [TextContent(type="text", text=result)]

# ==================== MCP SERVER STARTUP ====================

async def main():
    """Start MCP server."""
    print("🚀 Starting Company Data MCP Server...", flush=True)

    async with stdio_server() as (read_stream, write_stream):
        print("✅ MCP Server ready", flush=True)

        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="company-data-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
