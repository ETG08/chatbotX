#!/usr/bin/env python3
"""
Company Data Server - FastAPI Version
Serves company information from local JSON database.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional, List, Dict
import json
import os

app = FastAPI(
    title="Company Data Server",
    description="Local data source for company information",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load company data
DATA_FILE = "company_data.json"

def load_data():
    """Load company data from JSON file."""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Load data once at startup
COMPANY_DATA = load_data()

# ==================== HOME PAGE ====================

@app.get("/", response_class=HTMLResponse)
async def home():
    """
    Home page with API documentation.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Company Data Server</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
            }}
            h2 {{
                color: #667eea;
                margin-top: 30px;
                margin-bottom: 20px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }}
            .endpoint {{
                background: #f8f9fa;
                padding: 20px;
                margin: 15px 0;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                transition: all 0.3s;
            }}
            .endpoint:hover {{
                transform: translateX(5px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .method {{
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 10px;
                font-size: 0.9em;
            }}
            .path {{
                color: #333;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                font-size: 1.1em;
            }}
            .description {{
                color: #666;
                margin-top: 10px;
                line-height: 1.6;
            }}
            code {{
                background: #263238;
                color: #aed581;
                padding: 2px 8px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
            }}
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
            }}
            .stat-label {{
                margin-top: 5px;
                opacity: 0.9;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1> Company Data Server</h1>
            <p class="subtitle">Local data source for company information </p>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(COMPANY_DATA['employees'])}</div>
                    <div class="stat-label">Employees</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(COMPANY_DATA['departments'])}</div>
                    <div class="stat-label">Departments</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(COMPANY_DATA['holidays'])}</div>
                    <div class="stat-label">Holidays</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(COMPANY_DATA['announcements'])}</div>
                    <div class="stat-label">Announcements</div>
                </div>
            </div>

            <h2> Available API Endpoints</h2>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/employees</span>
                <div class="description">
                    Get all employees or search/filter<br>
                    Query parameters: <code>?search=John</code> <code>?department=Engineering</code>
                </div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/employees/{{employee_id}}</span>
                <div class="description">
                    Get specific employee by ID<br>
                    Example: <code>/api/employees/EMP001</code>
                </div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/departments</span>
                <div class="description">
                    Get list of all departments
                </div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/leave/{{employee_id}}</span>
                <div class="description">
                    Get leave balance for an employee<br>
                    Example: <code>/api/leave/EMP001</code>
                </div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/holidays</span>
                <div class="description">
                    Get company holidays for the year
                </div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/announcements</span>
                <div class="description">
                    Get recent announcements<br>
                    Query parameters: <code>?limit=5</code>
                </div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/policies</span>
                <div class="description">
                    Search company policies<br>
                    Query parameters: <code>?search=remote</code>
                </div>
            </div>

            <h2> Interactive Documentation</h2>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/docs</span>
                <div class="description">
                    FastAPI automatic interactive API documentation (Swagger UI)
                </div>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/redoc</span>
                <div class="description">
                    Alternative API documentation (ReDoc)
                </div>
            </div>

            <div class="footer">
                <p>Server Status: <strong style="color: #4caf50;">✓ Online</strong></p>
            </div>
        </div>
    </body>
    </html>
    """

# ==================== EMPLOYEE ENDPOINTS ====================

@app.get("/api/employees")
async def get_employees(
    search: Optional[str] = Query(None, description="Search by name, email, or ID"),
    department: Optional[str] = Query(None, description="Filter by department")
):
    """Get all employees or search/filter."""
    employees = COMPANY_DATA['employees']

    # Filter by search term (CASE-INSENSITIVE)
    if search:
        search_lower = search.lower()
        employees = [
            emp for emp in employees
            if search_lower in emp['firstName'].lower()
            or search_lower in emp['lastName'].lower()
            or search_lower in emp['email'].lower()
            or search_lower in emp['id'].lower()
            or search_lower in f"{emp['firstName']} {emp['lastName']}".lower()  # Search full name
        ]

    # Filter by department (CASE-INSENSITIVE)
    if department:
        dept_lower = department.lower()
        employees = [
            emp for emp in employees
            if dept_lower in emp['department'].lower()
        ]

    return {
        "data": employees,
        "count": len(employees)
    }
@app.get("/api/employees/{employee_id}")
async def get_employee_by_id(employee_id: str):
    """
    Get detailed information about a specific employee.

    - **employee_id**: Employee ID (e.g., EMP001)
    """
    employee = next(
        (emp for emp in COMPANY_DATA['employees'] if emp['id'] == employee_id),
        None
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail=f"Employee with ID '{employee_id}' not found"
        )

    return {"data": [employee]}

# ==================== DEPARTMENT ENDPOINTS ====================

@app.get("/api/departments")
async def get_departments():
    """Get list of all departments."""
    return {
        "data": COMPANY_DATA['departments'],
        "count": len(COMPANY_DATA['departments'])
    }

# ==================== LEAVE ENDPOINTS ====================

@app.get("/api/leave/{employee_id}")
async def get_leave_balance(employee_id: str):
    """
    Get leave balance for an employee.

    - **employee_id**: Employee ID (e.g., EMP001)
    """
    balance = COMPANY_DATA['leave_balances'].get(employee_id)

    if not balance:
        raise HTTPException(
            status_code=404,
            detail=f"Leave balance not found for employee '{employee_id}'"
        )

# Convert to list format
    leave_data = []
    for leave_type, details in balance.items():
        leave_data.append({
            "leaveType": leave_type,
            **details
        })

    return {"data": leave_data}

# ==================== HOLIDAY ENDPOINTS ====================

@app.get("/api/holidays")
async def get_holidays():
    """Get list of company holidays."""
    return {
        "data": COMPANY_DATA['holidays'],
        "count": len(COMPANY_DATA['holidays'])
    }

# ==================== ANNOUNCEMENT ENDPOINTS ====================

@app.get("/api/announcements")
async def get_announcements(
    limit: int = Query(10, description="Number of announcements to return", ge=1, le=50)
):
    """
    Get recent company announcements.

    - **limit**: Number of announcements to retrieve (default: 10, max: 50)
    """
    announcements = COMPANY_DATA['announcements'][:limit]

    return {
        "data": announcements,
        "count": len(announcements)
    }

# ==================== POLICY ENDPOINTS ====================

@app.get("/api/policies")
async def get_policies(
    search: Optional[str] = Query(None, description="Search policies by keyword")
):
    """
    Get company policies, optionally filtered by search term.

    - **search**: Search term for policy title, content, or category
    """
    policies = COMPANY_DATA['policies']

    if search:
        search_lower = search.lower()
        policies = [
            pol for pol in policies
            if search_lower in pol['title'].lower()
            or search_lower in pol['content'].lower()
            or search_lower in pol['category'].lower()
        ]

    return {
        "data": policies,
        "count": len(policies)
    }

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "server": "Company Data Server",
        "version": "1.0.0",
        "data_loaded": {
            "employees": len(COMPANY_DATA['employees']),
            "departments": len(COMPANY_DATA['departments']),
            "holidays": len(COMPANY_DATA['holidays']),
            "announcements": len(COMPANY_DATA['announcements']),
            "policies": len(COMPANY_DATA['policies'])
        }
    }

# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Run on startup."""
    print("\n" + "="*60)
    print("🚀 Company Data Server Starting...")
    print("="*60)
    print(f"📊 Loaded Data:")
    print(f"   - {len(COMPANY_DATA['employees'])} employees")
    print(f"   - {len(COMPANY_DATA['departments'])} departments")
    print(f"   - {len(COMPANY_DATA['holidays'])} holidays")
    print(f"   - {len(COMPANY_DATA['announcements'])} announcements")
    print(f"   - {len(COMPANY_DATA['policies'])} policies")
    print("="*60)
    print("✅ Server Ready!")
    print(f"📖 Open http://localhost:5000 for home page")
    print(f"📚 Open http://localhost:5000/docs for API documentation")
    print("="*60 + "\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
