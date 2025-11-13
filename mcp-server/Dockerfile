# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server file
COPY mcp_server.py .

# Make script executable
RUN chmod +x mcp_server.py

# The MCP server runs via stdio (launched by Emily's backend)
# For standalone testing:
CMD ["python", "mcp_server.py"]
