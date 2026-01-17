"""
Maven Service - Flask API Entry Point

CFO & CTO of Mother Haven - Treasury, Trading, and Technology.
Provides health, status, treasury tracking, and trading analysis endpoints.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Database connection (lazy load)
_db_connection = None

def get_db():
    """Get database connection."""
    global _db_connection
    if _db_connection is None:
        try:
            from database.connection import get_connection
            _db_connection = get_connection()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    return _db_connection

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
        identity_path = Path('/app/.moha/maven/identity.json')
        identity = {}
        if identity_path.exists():
            identity = json.loads(identity_path.read_text())

        return jsonify({
            'status': 'online',
            'name': identity.get('name', 'Maven'),
            'role': identity.get('role', 'CFO & CTO, First Second Employee'),
            'email': identity.get('email', 'maven@motherhaven.app'),
            'total_decisions': identity.get('total_decisions', 0),
            'titles': identity.get('titles', ['Chief Financial Officer', 'Chief Technology Officer']),
            'message': 'Maven online - ready to make money for moha'
        })
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'error': str(e)
        }), 500


# =============================================================================
# TREASURY ENDPOINTS
# =============================================================================

@app.route('/api/treasury/state', methods=['GET'])
def treasury_state():
    """Get current treasury state from database."""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM maven_treasury_current
        """)
        row = cursor.fetchone()
        cursor.close()

        if row:
            return jsonify({
                'wallet_address': row[0],
                'account_value_usd': float(row[1]) if row[1] else 0,
                'withdrawable_usd': float(row[2]) if row[2] else 0,
                'margin_used_usd': float(row[3]) if row[3] else 0,
                'unrealized_pnl_usd': float(row[4]) if row[4] else 0,
                'active_positions': row[5],
                'positions': row[6],
                'value_change_24h_usd': float(row[7]) if row[7] else None,
                'snapshot_at': row[8].isoformat() if row[8] else None
            })
        else:
            return jsonify({'message': 'No treasury data yet', 'account_value_usd': 0})
    except Exception as e:
        logger.error(f"Treasury state error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/treasury/performance', methods=['GET'])
def treasury_performance():
    """Get treasury performance over time."""
    try:
        days = request.args.get('days', 30, type=int)
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("SELECT * FROM maven_treasury_performance(%s)", (days,))
        row = cursor.fetchone()
        cursor.close()

        if row:
            return jsonify({
                'period_days': days,
                'start_value': float(row[0]) if row[0] else 0,
                'end_value': float(row[1]) if row[1] else 0,
                'absolute_change': float(row[2]) if row[2] else 0,
                'percentage_change': float(row[3]) if row[3] else 0,
                'high_water_mark': float(row[4]) if row[4] else 0,
                'low_water_mark': float(row[5]) if row[5] else 0,
                'snapshot_count': row[6]
            })
        else:
            return jsonify({'message': 'No performance data', 'period_days': days})
    except Exception as e:
        logger.error(f"Treasury performance error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/treasury/snapshot', methods=['POST'])
def record_treasury_snapshot():
    """Record a new treasury snapshot."""
    try:
        data = request.json
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("""
            SELECT maven_record_treasury_snapshot(%s, %s, %s, %s, %s)
        """, (
            data.get('account_value', 0),
            data.get('withdrawable', 0),
            data.get('margin_used', 0),
            data.get('unrealized_pnl', 0),
            json.dumps(data.get('positions', []))
        ))
        snapshot_id = cursor.fetchone()[0]
        db.commit()
        cursor.close()

        return jsonify({
            'success': True,
            'snapshot_id': snapshot_id,
            'message': 'Treasury snapshot recorded'
        })
    except Exception as e:
        logger.error(f"Treasury snapshot error: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# WATCHLIST ENDPOINTS
# =============================================================================

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """Get Maven's coin watchlist with latest prices."""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("SELECT * FROM maven_watchlist_prices")
        rows = cursor.fetchall()
        cursor.close()

        watchlist = []
        for row in rows:
            watchlist.append({
                'coin': row[0],
                'priority': row[1],
                'market_type': row[2],
                'mid_price': float(row[3]) if row[3] else None,
                'funding_rate': float(row[4]) if row[4] else None,
                'volume_24h_usd': float(row[5]) if row[5] else None,
                'price_updated_at': row[6].isoformat() if row[6] else None
            })

        return jsonify({'watchlist': watchlist, 'count': len(watchlist)})
    except Exception as e:
        logger.error(f"Watchlist error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """Add a coin to Maven's watchlist."""
    try:
        data = request.json
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO maven_watchlist (coin, market_type, priority, watch_reason, tags)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (coin) DO UPDATE SET
                priority = EXCLUDED.priority,
                watch_reason = EXCLUDED.watch_reason,
                tags = EXCLUDED.tags,
                active = TRUE,
                updated_at = NOW()
            RETURNING id
        """, (
            data['coin'].upper(),
            data.get('market_type', 'perp'),
            data.get('priority', 'normal'),
            data.get('reason', ''),
            data.get('tags', [])
        ))
        watch_id = cursor.fetchone()[0]
        db.commit()
        cursor.close()

        return jsonify({
            'success': True,
            'watch_id': watch_id,
            'coin': data['coin'].upper()
        })
    except Exception as e:
        logger.error(f"Add watchlist error: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# SIGNALS ENDPOINTS
# =============================================================================

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get active trading signals."""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("SELECT * FROM maven_active_signals LIMIT 50")
        rows = cursor.fetchall()
        cursor.close()

        signals = []
        for row in rows:
            signals.append({
                'coin': row[0],
                'source': row[1],
                'signal_type': row[2],
                'strength': float(row[3]) if row[3] else None,
                'reasoning': row[4],
                'generated_at': row[5].isoformat() if row[5] else None,
                'valid_until': row[6].isoformat() if row[6] else None
            })

        return jsonify({'signals': signals, 'count': len(signals)})
    except Exception as e:
        logger.error(f"Signals error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals', methods=['POST'])
def record_signal():
    """Record a new trading signal."""
    try:
        data = request.json
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO maven_trading_signals
            (signal_source, source_bot_id, coin, signal_type, strength, reasoning,
             indicators_used, market_context, valid_until, generated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            data.get('source', 'manual'),
            data.get('bot_id'),
            data['coin'].upper(),
            data['signal_type'],
            data.get('strength', 50),
            data.get('reasoning', ''),
            data.get('indicators', []),
            json.dumps(data.get('market_context', {})),
            data.get('valid_until')
        ))
        signal_id = cursor.fetchone()[0]
        db.commit()
        cursor.close()

        logger.info(f"Signal recorded: {data['coin']} {data['signal_type']} (ID: {signal_id})")

        return jsonify({
            'success': True,
            'signal_id': signal_id,
            'coin': data['coin'].upper(),
            'signal_type': data['signal_type']
        })
    except Exception as e:
        logger.error(f"Record signal error: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# DECISIONS ENDPOINTS
# =============================================================================

@app.route('/api/decisions', methods=['GET'])
def get_decisions():
    """Get recent Maven decisions."""
    try:
        limit = request.args.get('limit', 20, type=int)
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("""
            SELECT id, decision_type, asset, action, reasoning, confidence,
                   risk_level, executed, decided_at
            FROM maven_decisions
            ORDER BY decided_at DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        cursor.close()

        decisions = []
        for row in rows:
            decisions.append({
                'id': row[0],
                'decision_type': row[1],
                'asset': row[2],
                'action': row[3],
                'reasoning': row[4],
                'confidence': float(row[5]) if row[5] else None,
                'risk_level': row[6],
                'executed': row[7],
                'decided_at': row[8].isoformat() if row[8] else None
            })

        return jsonify({'decisions': decisions, 'count': len(decisions)})
    except Exception as e:
        logger.error(f"Decisions error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/decisions/performance', methods=['GET'])
def decision_performance():
    """Get decision performance summary."""
    try:
        days = request.args.get('days', 7, type=int)
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        cursor = db.cursor()
        cursor.execute("SELECT * FROM maven_decision_performance(%s)", (days,))
        rows = cursor.fetchall()
        cursor.close()

        performance = []
        for row in rows:
            performance.append({
                'decision_id': row[0],
                'decided_at': row[1].isoformat() if row[1] else None,
                'decision_type': row[2],
                'asset': row[3],
                'confidence': float(row[4]) if row[4] else None,
                'trades_executed': row[5],
                'total_pnl': float(row[6]) if row[6] else 0,
                'outcome': row[7]
            })

        return jsonify({
            'period_days': days,
            'decisions': performance,
            'count': len(performance)
        })
    except Exception as e:
        logger.error(f"Decision performance error: {e}")
        return jsonify({'error': str(e)}), 500


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
