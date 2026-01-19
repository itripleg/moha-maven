FROM python:3.11-slim

WORKDIR /app

# Install system dependencies: git, Node.js, npm, curl
RUN apt-get update && \
    apt-get install -y git curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Verify Node.js installation
RUN node --version && npm --version

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Install Maven CLI (creates 'maven' and 'maven-banner' commands)
RUN pip install -e .

# Expose ports: 3100 (MCP), 5002 (API)
EXPOSE 3100 5002

# Install supervisor to run both Flask API and MCP server
RUN pip install supervisor

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisor (runs Flask API + MCP server)
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
