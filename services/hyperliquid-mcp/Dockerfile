FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose MCP port
EXPOSE 3101

# Run the MCP server
CMD ["python", "main.py"]
