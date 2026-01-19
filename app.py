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

# Maven base directory for accessing git-first data
MAVEN_BASE_DIR = os.getenv('MAVEN_BASE_DIR', '/app')

# Import database connection context manager
try:
    from database.connection import get_db_connection as _get_db_connection
    CLAUDE_DB_AVAILABLE = True
except Exception as e:
    logger.error(f"Database import failed: {e}")
    _get_db_connection = None
    CLAUDE_DB_AVAILABLE = False

# Import email sending function
try:
    from maven_mcp.tools import _send_email
    EMAIL_AVAILABLE = True
except Exception as e:
    logger.error(f"Email tools import failed: {e}")
    _send_email = None
    EMAIL_AVAILABLE = False

def get_db():
    """Get database connection (returns connection object from pool)."""
    if not _get_db_connection:
        return None
    # Return a connection from the pool directly (not context manager)
    return _get_db_connection().__enter__()

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
# EMAIL INCOMING WEBHOOK
# =============================================================================

@app.route('/api/email/incoming', methods=['POST'])
def email_incoming():
    """
    Webhook endpoint for incoming emails to maven@motherhaven.app.

    Called by moha-next when SendGrid delivers an email to maven@.
    Logs the email and queues for processing.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        from_email = data.get('from', 'unknown')
        from_name = data.get('fromName', '')
        subject = data.get('subject', '(No Subject)')
        text_content = data.get('textContent', '')
        html_content = data.get('htmlContent', '')
        received_at = data.get('receivedAt', datetime.utcnow().isoformat())

        logger.info(f"📨 INCOMING EMAIL from {from_name} <{from_email}>")
        logger.info(f"   Subject: {subject}")

        # Save to git-first persistence
        email_dir = Path(MAVEN_BASE_DIR) / '.moha' / 'maven' / 'inbox'
        email_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_from = from_email.replace('@', '_at_').replace('.', '_')[:30]
        filename = f"email_{timestamp}_{safe_from}.json"

        email_record = {
            'from': from_email,
            'from_name': from_name,
            'subject': subject,
            'text_content': text_content,
            'html_content': html_content,
            'received_at': received_at,
            'processed': False,
            'logged_at': datetime.utcnow().isoformat()
        }

        with open(email_dir / filename, 'w') as f:
            json.dump(email_record, f, indent=2)

        logger.info(f"   Saved to: {filename}")

        # Log to session
        try:
            from maven_mcp.tools import _log_event
            _log_event(
                event_type='email_received',
                content=f"Email from {from_name or from_email}: {subject}",
                metadata={'from': from_email, 'subject': subject, 'file': filename}
            )
        except Exception as e:
            logger.warning(f"Could not log to session: {e}")

        return jsonify({
            'success': True,
            'message': 'Email received and logged',
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Email incoming error: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# NOTIFICATIONS ENDPOINTS
# =============================================================================

@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    """
    Send high-confidence signal notification via email.

    Called by moha-bot Maven scanner when confidence >= threshold.
    Uses Maven's MCP email tool to send from maven@motherhaven.app.

    Request body:
        {
            "opportunities": [...],  # List of high-confidence opportunities
            "confidence_threshold": 90,
            "recipient": "email@example.com"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        opportunities = data.get('opportunities', [])
        recipient = data.get('recipient')
        confidence_threshold = data.get('confidence_threshold', 90)

        if not opportunities:
            return jsonify({'error': 'No opportunities provided'}), 400

        if not recipient:
            return jsonify({'error': 'Recipient email required'}), 400

        # Build email content
        subject = _build_notification_subject(opportunities)
        html_content = _build_notification_html(opportunities, confidence_threshold)
        text_content = _build_notification_text(opportunities, confidence_threshold)

        # Send email via maven_send_email
        logger.info(f"📧 HIGH-CONFIDENCE ALERT: {len(opportunities)} signals >= {confidence_threshold}%")
        logger.info(f"To: {recipient}")
        logger.info(f"Subject: {subject}")

        # Actually send the email
        if EMAIL_AVAILABLE and _send_email:
            email_result = _send_email(
                to=recipient,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_name="Maven",
                from_email="maven@motherhaven.app"
            )

            if email_result.get('success'):
                logger.info(f"✅ Email sent successfully to {recipient}")
                return jsonify({
                    'status': 'sent',
                    'message': f'Email sent for {len(opportunities)} high-confidence signals',
                    'recipient': recipient,
                    'signal_count': len(opportunities)
                })
            else:
                # Email failed - queue for retry
                logger.error(f"❌ Email send failed: {email_result.get('error')}")
                _queue_notification(recipient, subject, html_content, text_content, opportunities)
                return jsonify({
                    'status': 'queued',
                    'message': f'Email failed, queued for retry: {email_result.get("error")}',
                    'recipient': recipient,
                    'signal_count': len(opportunities)
                })
        else:
            # Email not available - queue for manual pickup
            logger.warning("Email tools not available, queuing notification")
            _queue_notification(recipient, subject, html_content, text_content, opportunities)
            return jsonify({
                'status': 'queued',
                'message': f'Notification queued (email tools unavailable)',
                'recipient': recipient,
                'signal_count': len(opportunities)
            })

    except Exception as e:
        logger.error(f"Notification send error: {e}")
        return jsonify({'error': str(e)}), 500


def _build_notification_subject(opportunities):
    """Build notification email subject."""
    if len(opportunities) == 1:
        opp = opportunities[0]
        return f"🚨 Maven Alert: {opp['asset']} - {opp['maven_confidence']}% Confidence"
    else:
        max_conf = max(opp['maven_confidence'] for opp in opportunities)
        return f"🚨 Maven Alert: {len(opportunities)} High-Confidence Signals (up to {max_conf}%)"


def _build_notification_html(opportunities, threshold):
    """Build HTML email content for notifications."""
    opps_html = ""
    for i, opp in enumerate(opportunities, 1):
        conf_color = "#10b981" if opp['maven_confidence'] >= 95 else "#f59e0b"
        funding_info = f"<li><strong>Funding APR:</strong> {opp.get('funding_apr', 0):.1f}%</li>" if opp.get('funding_apr') else ""

        opps_html += f"""
        <div style="background: #1f2937; border-left: 4px solid {conf_color}; padding: 16px; margin-bottom: 16px; border-radius: 4px;">
            <h3 style="margin: 0 0 12px 0; color: #f3f4f6;">#{i}: {opp['asset']}</h3>
            <ul style="color: #d1d5db; line-height: 1.6; margin: 0; padding-left: 20px;">
                <li><strong>Confidence:</strong> <span style="color: {conf_color}; font-size: 18px; font-weight: bold;">{opp['maven_confidence']}%</span></li>
                <li><strong>Score:</strong> {opp.get('maven_score', 0):.2f}</li>
                <li><strong>Type:</strong> {opp.get('opportunity_type', 'N/A')}</li>
                <li><strong>Risk:</strong> {opp.get('risk_level', 'MEDIUM')}</li>
                <li><strong>Size:</strong> ${opp.get('position_size_usd', 0):,.0f}</li>
                {funding_info}
            </ul>
            <p style="color: #9ca3af; margin: 12px 0 0 0; font-style: italic;">{opp.get('reasoning', '')}</p>
        </div>
        """

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Maven Alert</title></head>
<body style="font-family: sans-serif; background: #111827; color: #f3f4f6; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: #1f2937; border-radius: 8px; padding: 24px;">
        <h1 style="color: #f59e0b; margin: 0 0 8px 0;">🚨 Maven High-Confidence Alert</h1>
        <p style="color: #9ca3af; margin: 0 0 24px 0; font-size: 14px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p style="color: #d1d5db; line-height: 1.6;">Maven detected <strong>{len(opportunities)}</strong> high-confidence signal{"s" if len(opportunities) != 1 else ""} (>= {threshold}%).</p>
        <div style="margin: 24px 0;">{opps_html}</div>
        <div style="margin-top: 24px; padding-top: 24px; border-top: 1px solid #374151; text-align: center;">
            <p style="margin: 0; color: #6b7280; font-size: 12px;">We're too smart to be poor. 💎<br>- Maven, HBIC, Mother Haven Treasury</p>
        </div>
    </div>
</body></html>"""


def _build_notification_text(opportunities, threshold):
    """Build plain text email content."""
    lines = [
        "🚨 MAVEN HIGH-CONFIDENCE ALERT",
        "=" * 50,
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Signals: {len(opportunities)} (>= {threshold}%)",
        "",
    ]

    for i, opp in enumerate(opportunities, 1):
        lines.append(f"#{i}: {opp['asset']}")
        lines.append(f"  Confidence: {opp['maven_confidence']}%")
        lines.append(f"  Score: {opp.get('maven_score', 0):.2f}")
        lines.append(f"  Size: ${opp.get('position_size_usd', 0):,.0f}")
        if opp.get('funding_apr'):
            lines.append(f"  Funding: {opp['funding_apr']:.1f}% APR")
        lines.append(f"  {opp.get('reasoning', '')}")
        lines.append("")

    lines.extend(["=" * 50, "We're too smart to be poor. 💎", "- Maven, HBIC"])
    return "\n".join(lines)


def _queue_notification(recipient, subject, html_content, text_content, opportunities):
    """Save notification to queue for Claude Code to send via MCP."""
    import json
    from pathlib import Path

    notifications_dir = Path('/app/.moha/maven/notifications')
    notifications_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    notification_file = notifications_dir / f'signal_{timestamp}.json'

    notification = {
        'type': 'high_confidence_signal',
        'timestamp': datetime.now().isoformat(),
        'recipient': recipient,
        'subject': subject,
        'html_content': html_content,
        'text_content': text_content,
        'opportunities': opportunities,
        'sent': False
    }

    with open(notification_file, 'w') as f:
        json.dump(notification, f, indent=2)

    logger.info(f"📧 Queued: {notification_file}")


@app.route('/api/notifications/pending', methods=['GET'])
def get_pending_notifications():
    """Get list of pending (unsent) notifications."""
    try:
        from pathlib import Path
        import json

        notifications_dir = Path('/app/.moha/maven/notifications')
        if not notifications_dir.exists():
            return jsonify({'pending': [], 'count': 0})

        pending = []
        for notification_file in sorted(notifications_dir.glob('signal_*.json')):
            try:
                with open(notification_file, 'r') as f:
                    notification = json.load(f)

                if not notification.get('sent', False):
                    pending.append({
                        'file': notification_file.name,
                        'timestamp': notification['timestamp'],
                        'recipient': notification['recipient'],
                        'subject': notification['subject'],
                        'signal_count': len(notification.get('opportunities', []))
                    })
            except Exception as e:
                logger.error(f"Error reading notification {notification_file}: {e}")

        return jsonify({
            'pending': pending,
            'count': len(pending)
        })

    except Exception as e:
        logger.error(f"Get pending notifications error: {e}")
        return jsonify({'error': str(e)}), 500


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


# =============================================================================
# MCP Resource Endpoints (HTTP Access to MCP Data)
# =============================================================================

@app.route('/api/mcp/identity', methods=['GET'])
def mcp_identity():
    """Get Maven's identity (mirrors maven://identity MCP resource)."""
    try:
        identity_path = os.path.join(MAVEN_BASE_DIR, '.moha', 'maven', 'identity.json')
        if os.path.exists(identity_path):
            with open(identity_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({
                'name': 'Maven',
                'role': 'AI CFO',
                'status': 'initializing',
                'total_decisions': 0,
                'rebirth_count': 0
            })
    except Exception as e:
        logger.error(f"Identity read error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mcp/memory', methods=['GET'])
def mcp_memory():
    """Get Maven's session log (mirrors maven://memory MCP resource)."""
    try:
        memory_path = os.path.join(MAVEN_BASE_DIR, '.moha', 'maven', 'session_log.md')
        lines = request.args.get('lines', type=int)  # Optional: return last N lines

        if os.path.exists(memory_path):
            with open(memory_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if lines:
                # Return last N lines
                all_lines = content.splitlines()
                content = '\n'.join(all_lines[-lines:])

            return content, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
        else:
            return "# Maven Session Log\n\nNo events recorded yet.", 200, {
                'Content-Type': 'text/markdown; charset=utf-8'
            }
    except Exception as e:
        logger.error(f"Memory read error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mcp/infrastructure', methods=['GET'])
def mcp_infrastructure():
    """Get Maven's infrastructure knowledge (mirrors maven://infrastructure MCP resource)."""
    try:
        infra_path = os.path.join(MAVEN_BASE_DIR, '.moha', 'maven', 'infrastructure.json')
        if os.path.exists(infra_path):
            with open(infra_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({'error': 'Infrastructure data not found'}), 404
    except Exception as e:
        logger.error(f"Infrastructure read error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mcp/decisions/recent', methods=['GET'])
def mcp_recent_decisions():
    """Get Maven's recent decisions (mirrors maven://decisions MCP resource)."""
    try:
        decisions_dir = os.path.join(MAVEN_BASE_DIR, '.moha', 'maven', 'decisions')
        limit = request.args.get('limit', 10, type=int)

        if os.path.exists(decisions_dir):
            # Get all decision files sorted by modification time
            decision_files = []
            for filename in os.listdir(decisions_dir):
                if filename.endswith('.md') and filename != '.gitkeep':
                    filepath = os.path.join(decisions_dir, filename)
                    decision_files.append((filepath, os.path.getmtime(filepath)))

            # Sort by modification time (newest first)
            decision_files.sort(key=lambda x: x[1], reverse=True)

            # Read recent decisions
            decisions = []
            for filepath, _ in decision_files[:limit]:
                with open(filepath, 'r', encoding='utf-8') as f:
                    decisions.append({
                        'filename': os.path.basename(filepath),
                        'content': f.read()
                    })

            return jsonify({
                'count': len(decisions),
                'decisions': decisions
            })
        else:
            return jsonify({'count': 0, 'decisions': []})
    except Exception as e:
        logger.error(f"Recent decisions read error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mcp/trading-setup', methods=['GET'])
def mcp_trading_setup():
    """Get Maven's trading setup documentation."""
    try:
        setup_path = os.path.join(MAVEN_BASE_DIR, '.moha', 'maven', 'TRADING_SETUP.md')
        if os.path.exists(setup_path):
            with open(setup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
        else:
            return "# Trading Setup\n\nNo setup documentation found.", 200, {
                'Content-Type': 'text/markdown; charset=utf-8'
            }
    except Exception as e:
        logger.error(f"Trading setup read error: {e}")
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
