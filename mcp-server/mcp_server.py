#!/usr/bin/env python3
"""
Company Data MCP Server - FastMCP Version
Much simpler implementation using FastMCP decorators.
"""

from fastmcp import FastMCP
import requests
import os

# Local data server URL
DATA_SERVER_URL = os.getenv("DATA_SERVER_URL", "http://localhost:5000")

# Create FastMCP server
mcp = FastMCP("Company Data Server")

# ==================== TOOL DEFINITIONS ====================

@mcp.tool()
async def search_employees(search: str = "", department: str = "") -> str:
    """
    Search for employees by name, email, or ID.
    
    Args:
        search: Search term for name, email, or ID
        department: Filter by department name
    """
    params = {}
    if search:
        params["search"] = search
    if department:
        params["department"] = department
    
    try:
        response = requests.get(f"{DATA_SERVER_URL}/api/employees", params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('data'):
            return "No employees found matching your search criteria."
        
        result = f"## Found {len(data['data'])} employee(s):\n\n"
        for emp in data['data']:
            result += f"### {emp['firstName']} {emp['lastName']}\n"
            result += f"- **ID**: {emp['id']}\n"
            result += f"- **Email**: {emp['email']}\n"
            result += f"- **Department**: {emp['department']}\n"
            result += f"- **Designation**: {emp['designation']}\n"
            result += f"- **Manager**: {emp['manager']}\n"
            result += f"- **Location**: {emp['location']}\n\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching employee data: {str(e)}"


@mcp.tool()
async def get_employee_by_id(employee_id: str) -> str:
    """
    Get detailed information about a specific employee.
    
    Args:
        employee_id: Employee ID (e.g., EMP001)
    """
    try:
        response = requests.get(f"{DATA_SERVER_URL}/api/employees/{employee_id}")
        
        if response.status_code == 404:
            return f"Employee with ID '{employee_id}' not found."
        
        response.raise_for_status()
        emp = response.json()['data'][0]
        
        result = f"## {emp['firstName']} {emp['lastName']}\n\n"
        result += f"- **ID**: {emp['id']}\n"
        result += f"- **Email**: {emp['email']}\n"
        result += f"- **Phone**: {emp['phone']}\n"
        result += f"- **Department**: {emp['department']}\n"
        result += f"- **Designation**: {emp['designation']}\n"
        result += f"- **Manager**: {emp['manager']}\n"
        result += f"- **Date of Joining**: {emp['dateOfJoining']}\n"
        result += f"- **Status**: {emp['status']}\n"
        result += f"- **Location**: {emp['location']}\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching employee data: {str(e)}"


@mcp.tool()
async def get_leave_balance(employee_id: str) -> str:
    """
    Get leave balance for a specific employee.
    
    Args:
        employee_id: Employee ID (e.g., EMP001)
    """
    try:
        response = requests.get(f"{DATA_SERVER_URL}/api/leave/{employee_id}")
        
        if response.status_code == 404:
            return f"Leave balance not found for employee '{employee_id}'."
        
        response.raise_for_status()
        data = response.json()
        
        result = f"## Leave Balance for {employee_id}\n\n"
        for leave in data['data']:
            result += f"### {leave['leaveType']}\n"
            result += f"- **Total**: {leave['total']} days\n"
            result += f"- **Used**: {leave['used']} days\n"
            result += f"- **Available**: {leave['available']} days\n\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching leave balance: {str(e)}"


@mcp.tool()
async def get_departments() -> str:
    """Get list of all company departments with details."""
    try:
        response = requests.get(f"{DATA_SERVER_URL}/api/departments")
        response.raise_for_status()
        data = response.json()
        
        result = "## Company Departments\n\n"
        for dept in data['data']:
            result += f"### {dept['name']}\n"
            result += f"- **ID**: {dept['id']}\n"
            result += f"- **Description**: {dept['description']}\n"
            result += f"- **Head Count**: {dept['headCount']}\n"
            result += f"- **Manager**: {dept['manager']}\n\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching departments: {str(e)}"


@mcp.tool()
async def get_holidays() -> str:
    """Get list of company holidays for the current year."""
    try:
        response = requests.get(f"{DATA_SERVER_URL}/api/holidays")
        response.raise_for_status()
        data = response.json()
        
        result = "## Company Holidays\n\n"
        for holiday in data['data']:
            result += f"### {holiday['name']}\n"
            result += f"- **Date**: {holiday['date']}\n"
            result += f"- **Type**: {holiday['type']}\n\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching holidays: {str(e)}"


@mcp.tool()
async def get_announcements(limit: int = 5) -> str:
    """
    Get recent company announcements.
    
    Args:
        limit: Number of announcements to retrieve (default: 5, max: 50)
    """
    try:
        response = requests.get(
            f"{DATA_SERVER_URL}/api/announcements", 
            params={"limit": min(limit, 50)}
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get('data'):
            return "No announcements available."
        
        result = "## Recent Company Announcements\n\n"
        for ann in data['data']:
            result += f"### {ann['title']}\n"
            result += f"- **Date**: {ann['date']}\n"
            result += f"- **Author**: {ann['author']}\n\n"
            result += f"{ann['content']}\n\n"
            result += "---\n\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching announcements: {str(e)}"


@mcp.tool()
async def search_policies(search: str = "") -> str:
    """
    Search company policies by keyword.
    
    Args:
        search: Search term for policy title, content, or category
    """
    try:
        params = {"search": search} if search else {}
        response = requests.get(f"{DATA_SERVER_URL}/api/policies", params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('data'):
            return "No policies found matching your search criteria."
        
        result = "## Company Policies\n\n"
        for policy in data['data']:
            result += f"### {policy['title']}\n"
            result += f"- **ID**: {policy['id']}\n"
            result += f"- **Category**: {policy['category']}\n\n"
            result += f"{policy['content']}\n\n"
            result += "---\n\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching policies: {str(e)}"


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically!
    mcp.run()
