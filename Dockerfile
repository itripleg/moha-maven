FROM python:3.11-slim

WORKDIR /app

# Install git (needed for git persistence)
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Expose ports: 3100 (MCP), 5002 (API)
EXPOSE 3100 5002

# Install supervisor to run both Flask API and MCP server
RUN pip install supervisor

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisor (runs Flask API + MCP server)
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
