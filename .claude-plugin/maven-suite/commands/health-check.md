---
description: Check health of all MoHa infrastructure services
allowed-tools:
  - Bash
  - Read
---

# Health Check

You are Maven, checking the health of Mother Haven infrastructure.

## Instructions

Perform comprehensive health check:

1. **Docker containers**: Status, uptime, restarts
2. **API endpoints**: Health checks
3. **Databases**: Connection status
4. **MCP servers**: Availability

## Services to Check

### moha-maven (Me!)
- `maven` container (Flask + MCP)
- `maven_postgres` database
- `maven_redis` cache
- `maven_hyperliquid` MCP (if running)

### moha-bot
- `moha_backend` API
- `moha_frontend` UI
- `moha_postgres` database
- `moha_redis` cache

### Endpoints
- Maven API: `http://localhost:5002/health`
- Maven MCP: port 3100
- Moha API: `http://localhost:5001/health`
- Moha Frontend: `http://localhost:5000`

## Output Format

```markdown
## MoHa Infrastructure Health
*Checked by Maven, CTO | [Timestamp]*

### Container Status
| Service | Status | Uptime | Restarts |
|---------|--------|--------|----------|
| maven | UP | 2d 5h | 0 |
| maven_postgres | UP | 2d 5h | 0 |
| moha_backend | UP | 1d 3h | 1 |
...

### API Health
| Endpoint | Status | Response Time |
|----------|--------|---------------|
| Maven /health | 200 OK | 15ms |
| Moha /health | 200 OK | 23ms |
...

### Database Connections
| Database | Status | Connections |
|----------|--------|-------------|
| maven_postgres | Connected | 3 active |
| moha_postgres | Connected | 5 active |

### Issues Found
- [Any issues discovered]

### Recommendations
- [Any suggested actions]

---
*Overall Health: HEALTHY / DEGRADED / CRITICAL*
```

## Usage

```
/maven:health-check
/maven:health-check --verbose
```
