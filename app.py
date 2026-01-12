"""
Maven Service - Minimal Flask API Entry Point

Provides basic health check and status endpoints.
Full API routes will be added by auto-claude.
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
import sys

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container orchestration."""
    return jsonify({
        'status': 'healthy',
        'service': 'maven',
        'version': '1.0.0',
        'mcp_server': 'running on port 3100'
    })

@app.route('/api/maven/status', methods=['GET'])
def maven_status():
    """Maven's current status."""
    try:
        # Try to load identity
        from pathlib import Path
        import json

        identity_path = Path('/app/.moha/maven/identity.json')
        identity = {}
        if identity_path.exists():
            identity = json.loads(identity_path.read_text())

        return jsonify({
            'status': 'online',
            'name': identity.get('name', 'Maven'),
            'role': identity.get('role', 'Chief Financial Officer'),
            'email': identity.get('contact', {}).get('email', 'maven@motherhaven.app'),
            'total_decisions': identity.get('performance_tracking', {}).get('total_decisions', 0),
            'message': '💎 Maven online - ready to serve'
        })
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('MAVEN_API_PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'

    print("=" * 70)
    print("💎 MAVEN SERVICE STARTING 💎")
    print("=" * 70)
    print(f"Flask API: http://0.0.0.0:{port}")
    print(f"MCP Server: port 3100")
    print(f"Debug mode: {debug}")
    print("=" * 70)

    app.run(host='0.0.0.0', port=port, debug=debug)
