# Maven MCP Wrapper Script
# Wraps docker exec -i to avoid flag parsing issues with claude mcp add

docker exec -i maven python -m maven_mcp.server
