"""
Flask API for motherhaven v2.
Controls the trading bot and provides data endpoints.
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
from datetime import datetime
from eth_account import Account
from config import settings
from bot import bot, BotState

app = Flask(__name__)
CORS(app)

# Initialize database on startup
from database import init_database, set_database_path, seed_defaults
set_database_path(settings.trading_mode)
init_database()
seed_defaults()
print(f"[DATABASE] Initialized: {settings.trading_mode} mode")


# ============================================================================
# WEB INTERFACE
# ============================================================================

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Trading bot dashboard."""
    return render_template('pages/dashboard.html')


@app.route('/strategy')
def strategy():
    """Trading strategy configuration."""
    return render_template('pages/strategy.html')


@app.route('/database')
def database_page():
    """Database management."""
    return render_template('pages/database.html')


@app.route('/api-docs')
def api_docs():
    """API documentation."""
    return render_template('pages/api.html')


@app.route('/settings')
def settings_page():
    """Bot settings."""
    return render_template('pages/settings.html')


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


@app.route('/api/wallet')
def api_wallet():
    """Get configured wallet address."""
    wallet_address = None
    if settings.hyperliquid_wallet_private_key:
        try:
            account = Account.from_key(settings.hyperliquid_wallet_private_key)
            wallet_address = account.address
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({
        'address': wallet_address,
        'testnet': settings.hyperliquid_testnet,
        'trading_mode': settings.trading_mode
    })


@app.route('/api/status')
def api_status():
    """Get bot status."""
    bot_status = bot.get_status()

    # Get wallet address
    wallet_address = None
    if settings.hyperliquid_wallet_private_key:
        try:
            account = Account.from_key(settings.hyperliquid_wallet_private_key)
            wallet_address = account.address
        except:
            pass

    return jsonify({
        'bot': bot_status,
        'version': '2.0.0',
        'wallet': {
            'address': wallet_address,
            'testnet': settings.hyperliquid_testnet
        },
        'environment': {
            'has_hyperliquid_key': bool(settings.hyperliquid_wallet_private_key),
            'has_anthropic_key': bool(settings.anthropic_api_key),
            'trading_mode': settings.trading_mode,
            'testnet': settings.hyperliquid_testnet,
            'max_position_size_usd': settings.max_position_size_usd,
            'max_leverage': settings.max_leverage,
            'execution_interval_seconds': settings.execution_interval_seconds,
            'trading_assets': settings.get_trading_assets()
        }
    })


@app.route('/api/account')
def api_account():
    """Get account balance and PnL summary."""
    from database import query_latest_positions, query_account_states

    # Get latest account state if available
    account_states = query_account_states(limit=1)

    # Calculate totals from positions
    positions = query_latest_positions(limit=100)

    realized_pnl = 0.0
    unrealized_pnl = 0.0

    for pos in positions:
        if pos.get('status') == 'closed' and pos.get('pnl'):
            realized_pnl += pos['pnl']
        elif pos.get('status') == 'open' and pos.get('pnl'):
            unrealized_pnl += pos['pnl']

    # Use account state if available, otherwise show placeholder
    if account_states and len(account_states) > 0:
        latest_state = account_states[0]
        balance_usd = latest_state.get('balance', 0.0) or latest_state.get('account_value', 0.0)
        is_connected = True
    else:
        # Placeholder - trading logic not yet implemented
        balance_usd = 0.0
        is_connected = False

    return jsonify({
        'balance_usd': balance_usd,
        'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_pnl,
        'total_pnl': realized_pnl + unrealized_pnl,
        'is_connected': is_connected,
        'note': None if is_connected else 'Trading logic not yet implemented - connect to Hyperliquid for live data'
    })


@app.route('/api/bot/status')
def api_bot_status():
    """Alias for /api/status for backward compatibility."""
    return api_status()


# ============================================================================
# BOT CONTROL
# ============================================================================

@app.route('/api/bot/start', methods=['POST'])
def api_bot_start():
    """Start the trading bot."""
    try:
        bot.start()
        return jsonify({
            'success': True,
            'message': 'Bot started successfully',
            'status': bot.get_status()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/bot/pause', methods=['POST'])
def api_bot_pause():
    """Pause the trading bot."""
    try:
        bot.pause()
        return jsonify({
            'success': True,
            'message': 'Bot paused',
            'status': bot.get_status()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/bot/resume', methods=['POST'])
def api_bot_resume():
    """Resume the paused bot."""
    try:
        bot.resume()
        return jsonify({
            'success': True,
            'message': 'Bot resumed',
            'status': bot.get_status()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/bot/stop', methods=['POST'])
def api_bot_stop():
    """Stop the trading bot."""
    try:
        bot.stop()
        return jsonify({
            'success': True,
            'message': 'Bot stopped',
            'status': bot.get_status()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ============================================================================
# USER INPUT / COMMAND LISTENING
# ============================================================================

@app.route('/api/user_input', methods=['GET', 'POST', 'DELETE'])
def api_user_input():
    """Get active user input, save new input, or clear input."""
    from database import get_active_user_input, save_user_input, archive_user_input

    if request.method == 'GET':
        active_input = get_active_user_input()
        return jsonify(active_input if active_input else {})

    elif request.method == 'POST':
        data = request.json
        message = data.get('message')
        message_type = data.get('message_type', 'cycle')  # 'cycle' or 'interrupt'
        image_path = data.get('image_path')  # Optional path to uploaded image

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        if message_type not in ['cycle', 'interrupt']:
            return jsonify({'error': 'message_type must be "cycle" or "interrupt"'}), 400

        input_id = save_user_input(message, message_type, image_path)

        # If interrupt type (direct query), trigger immediate response
        if message_type == 'interrupt':
            from llm.direct_query import handle_direct_query

            try:
                # Get bot's immediate response to the query
                response = handle_direct_query(message, image_path)

                return jsonify({
                    'success': True,
                    'id': input_id,
                    'message': 'Query sent',
                    'message_type': message_type,
                    'response': response  # Return bot's answer immediately
                })
            except Exception as e:
                print(f"[ERROR] Direct query failed: {e}")
                return jsonify({
                    'success': True,
                    'id': input_id,
                    'message': 'Query saved but response failed',
                    'message_type': message_type,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'id': input_id,
            'message': 'User input saved',
            'message_type': message_type
        })

    elif request.method == 'DELETE':
        # Archive current active input if exists
        active_input = get_active_user_input()
        if active_input:
            archive_user_input(active_input['id'])
            return jsonify({'success': True, 'message': 'User input cleared'})
        return jsonify({'success': True, 'message': 'No active input to clear'})


@app.route('/api/upload_image', methods=['POST'])
def api_upload_image():
    """Upload an image for chart analysis."""
    from pathlib import Path
    from werkzeug.utils import secure_filename
    from datetime import datetime

    UPLOAD_FOLDER = Path(__file__).parent / 'data' / 'uploads'
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"chart_{timestamp}.{ext}"
        filepath = UPLOAD_FOLDER / filename

        file.save(str(filepath))

        return jsonify({
            'success': True,
            'filename': filename,
            'path': str(filepath)
        })
    else:
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400


# ============================================================================
# DATA ENDPOINTS - CANDLES
# ============================================================================

@app.route('/api/candles', methods=['GET', 'POST'])
def api_candles():
    """Get or save candle data."""
    from database import save_candle, query_candles

    if request.method == 'POST':
        data = request.json
        required = ['asset', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        try:
            save_candle(
                asset=data['asset'],
                timeframe=data['timeframe'],
                timestamp=data['timestamp'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data.get('volume')
            )
            return jsonify({'success': True, 'message': 'Candle saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        asset = request.args.get('asset')
        timeframe = request.args.get('timeframe')
        limit = int(request.args.get('limit', 100))

        if not asset or not timeframe:
            return jsonify({'error': 'asset and timeframe parameters required'}), 400

        try:
            candles = query_candles(asset, timeframe, limit)
            return jsonify({'candles': candles, 'count': len(candles)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# DATA ENDPOINTS - INDICATORS
# ============================================================================

@app.route('/api/indicators', methods=['GET', 'POST'])
def api_indicators():
    """Get or save indicator data."""
    from database import save_indicator, query_indicators

    if request.method == 'POST':
        data = request.json
        required = ['asset', 'timeframe', 'indicator_type', 'value']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        try:
            save_indicator(
                asset=data['asset'],
                timeframe=data['timeframe'],
                indicator_type=data['indicator_type'],
                value=data['value'],
                metadata=data.get('metadata')
            )
            return jsonify({'success': True, 'message': 'Indicator saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        asset = request.args.get('asset')
        timeframe = request.args.get('timeframe')
        indicator_type = request.args.get('indicator_type')
        limit = int(request.args.get('limit', 100))

        if not asset or not timeframe:
            return jsonify({'error': 'asset and timeframe parameters required'}), 400

        try:
            indicators = query_indicators(asset, timeframe, indicator_type, limit)
            return jsonify({'indicators': indicators, 'count': len(indicators)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# DATA ENDPOINTS - MARKET DATA
# ============================================================================

@app.route('/api/market-data', methods=['GET', 'POST'])
def api_market_data():
    """Get or save market snapshot data."""
    from database import save_market_snapshot, query_market_snapshots

    if request.method == 'POST':
        data = request.json
        required = ['asset', 'price']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        try:
            import json
            save_market_snapshot(
                asset=data['asset'],
                price=data['price'],
                volume_24h=data.get('volume_24h'),
                funding_rate=data.get('funding_rate'),
                open_interest=data.get('open_interest'),
                data=json.dumps(data.get('data')) if data.get('data') else None
            )
            return jsonify({'success': True, 'message': 'Market data saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        asset = request.args.get('asset')
        limit = int(request.args.get('limit', 100))

        if not asset:
            return jsonify({'error': 'asset parameter required'}), 400

        try:
            snapshots = query_market_snapshots(asset, limit)
            return jsonify({'snapshots': snapshots, 'count': len(snapshots)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# DATA ENDPOINTS - ACCOUNT STATES
# ============================================================================

@app.route('/api/account-states', methods=['GET', 'POST'])
def api_account_states():
    """Get or save account state snapshots."""
    from database import save_account_state, query_account_states

    if request.method == 'POST':
        data = request.json

        try:
            import json
            save_account_state(
                balance=data.get('balance'),
                equity=data.get('equity'),
                margin_used=data.get('margin_used'),
                available_margin=data.get('available_margin'),
                unrealized_pnl=data.get('unrealized_pnl'),
                realized_pnl=data.get('realized_pnl'),
                total_pnl=data.get('total_pnl'),
                account_value=data.get('account_value'),
                data=json.dumps(data.get('data')) if data.get('data') else None
            )
            return jsonify({'success': True, 'message': 'Account state saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        limit = int(request.args.get('limit', 100))

        try:
            states = query_account_states(limit)
            return jsonify({'account_states': states, 'count': len(states)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# DATA ENDPOINTS - VISIONS
# ============================================================================

@app.route('/api/visions', methods=['GET', 'POST'])
def api_visions():
    """Get or save trading visions."""
    from database import save_vision, query_visions

    if request.method == 'POST':
        data = request.json
        required = ['asset', 'vision_text']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        try:
            save_vision(
                asset=data['asset'],
                vision_text=data['vision_text'],
                market_context=data.get('market_context'),
                ta_summary=data.get('ta_summary')
            )
            return jsonify({'success': True, 'message': 'Vision saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        asset = request.args.get('asset')
        limit = int(request.args.get('limit', 10))

        if not asset:
            return jsonify({'error': 'asset parameter required'}), 400

        try:
            visions = query_visions(asset, limit)
            return jsonify({'visions': visions, 'count': len(visions)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# DATA ENDPOINTS - POSITIONS
# ============================================================================

@app.route('/api/positions', methods=['GET', 'POST', 'PUT'])
def api_positions():
    """Get, create, or update position data."""
    from database import query_latest_positions, create_position, update_position
    from eth_account import Account

    if request.method == 'POST':
        # Create a new position
        data = request.json
        required = ['asset', 'side', 'entry_price', 'size']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        # Validate side
        if data['side'] not in ['long', 'short']:
            return jsonify({'error': 'side must be "long" or "short"'}), 400

        try:
            # Get wallet address if available
            wallet_address = None
            if settings.hyperliquid_wallet_private_key:
                try:
                    account = Account.from_key(settings.hyperliquid_wallet_private_key)
                    wallet_address = account.address
                except:
                    pass

            position_id = create_position(
                asset=data['asset'],
                side=data['side'],
                entry_price=float(data['entry_price']),
                size=float(data['size']),
                leverage=float(data.get('leverage', 1.0)),
                wallet_address=wallet_address,
                initiated_by=data.get('initiated_by', 'api')
            )

            return jsonify({
                'success': True,
                'message': 'Position created',
                'position_id': position_id
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        # Update an existing position
        data = request.json
        position_id = data.get('position_id')

        if not position_id:
            return jsonify({'error': 'position_id is required'}), 400

        try:
            update_position(
                position_id=int(position_id),
                current_price=data.get('current_price'),
                pnl=data.get('pnl'),
                pnl_percent=data.get('pnl_percent'),
                status=data.get('status')
            )

            return jsonify({
                'success': True,
                'message': 'Position updated'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        limit = int(request.args.get('limit', 10))
        try:
            positions = query_latest_positions(limit)
            return jsonify({'positions': positions, 'count': len(positions)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# DATA ENDPOINTS - DECISIONS
# ============================================================================

@app.route('/api/decisions', methods=['GET', 'POST'])
def api_decisions():
    """Get or save trading decisions."""
    from database import save_trading_decision, query_trading_decisions

    if request.method == 'POST':
        data = request.json
        required = ['asset', 'decision']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        try:
            save_trading_decision(
                asset=data['asset'],
                decision=data['decision'],
                reasoning=data.get('reasoning', ''),
                confidence=data.get('confidence', 0.0),
                strategy_mode=data.get('strategy_mode'),
                cycle_number=data.get('cycle_number')
            )
            return jsonify({'success': True, 'message': 'Decision saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        asset = request.args.get('asset')
        limit = int(request.args.get('limit', 100))

        try:
            decisions = query_trading_decisions(asset=asset, limit=limit)
            return jsonify({'decisions': decisions, 'count': len(decisions)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# DATA ENDPOINTS - PROMPTS
# ============================================================================

@app.route('/api/prompts', methods=['GET', 'POST', 'PUT'])
def api_prompts():
    """Get, save, or update prompts."""
    from database import save_prompt, query_active_prompts, get_connection

    if request.method == 'POST':
        data = request.json
        required = ['prompt_type', 'prompt_text']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        valid_types = ['cooperative', 'hedging', 'entry_exit', 'date_collecting']
        if data['prompt_type'] not in valid_types:
            return jsonify({'error': f'prompt_type must be one of: {valid_types}'}), 400

        try:
            prompt_id = save_prompt(data['prompt_type'], data['prompt_text'])
            return jsonify({'success': True, 'message': 'Prompt saved', 'id': prompt_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        # Update existing active prompt
        data = request.json
        required = ['prompt_type', 'prompt_text']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        valid_types = ['cooperative', 'hedging', 'entry_exit', 'date_collecting']
        
        # Determine actual strategy type (could be a custom preset name)
        strategy_type = data['prompt_type']
        is_custom_preset = False
        
        if strategy_type not in valid_types:
            # Check if it's a custom preset
            print(f"[DEBUG] Checking custom preset for type: {strategy_type}")
            try:
                from database import get_strategy_preset, save_strategy_preset
                preset = get_strategy_preset(strategy_type)
                
                if preset:
                    is_custom_preset = True
                    strategy_type = preset['strategy_type']
                    # Update the preset definition itself
                    print(f"[DEBUG] Updating custom preset: {preset['name']}")
                    save_strategy_preset(
                        name=preset['name'],
                        strategy_type=preset['strategy_type'], 
                        prompt_text=data['prompt_text'],
                        description=preset['description']
                    )
                else:
                    return jsonify({'error': f'prompt_type must be one of {valid_types} or a valid custom preset name'}), 400
            except Exception as e:
                print(f"[DEBUG] Error updating custom preset: {e}")
                return jsonify({'error': f'Custom preset error: {str(e)}'}), 500

        try:
            # Deactivate all existing prompts of this type
            conn = get_connection()
            cursor = conn.cursor()

            table_map = {
                'cooperative': 'prompts_cooperative',
                'hedging': 'prompts_hedging',
                'entry_exit': 'prompts_entry_exit',
                'date_collecting': 'prompts_date_collecting'
            }

            table_name = table_map[strategy_type]

            # Deactivate old prompts
            cursor.execute(f"UPDATE {table_name} SET active = 0")

            # Insert new prompt as active
            cursor.execute(f"""
                INSERT INTO {table_name} (prompt_text, active)
                VALUES (?, 1)
            """, (data['prompt_text'],))

            prompt_id = cursor.lastrowid
            conn.commit()
            conn.close()

            message = 'Prompt updated'
            if is_custom_preset:
                message += ' and preset saved'

            return jsonify({'success': True, 'message': message, 'id': prompt_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        prompt_type = request.args.get('prompt_type')

        if not prompt_type:
            return jsonify({'error': 'prompt_type parameter required'}), 400

        try:
            prompts = query_active_prompts(prompt_type)
            return jsonify({'prompts': prompts, 'count': len(prompts)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# DATABASE MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/database/status')
def api_database_status():
    """Get database connection status and statistics."""
    from database import get_connection, get_db_path
    import os

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get table counts
        stats = {}
        tables = ['positions', 'candles', 'indicators', 'trading_decisions',
                 'market_snapshots', 'visions', 'bot_status', 'bot_config',
                 'prompts_cooperative', 'prompts_hedging', 'prompts_entry_exit', 'prompts_date_collecting',
                 'user_input', 'account_states']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]

        # Get open positions count
        cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
        open_positions = cursor.fetchone()[0]

        conn.close()

        # Get database file size
        db_path = get_db_path()
        db_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        db_size_mb = db_size_bytes / (1024 * 1024)

        return jsonify({
            'connected': True,
            'database': 'SQLite',
            'database_path': db_path,
            'database_size_bytes': db_size_bytes,
            'database_size_mb': round(db_size_mb, 2),
            'tables': stats,
            'table_counts': {
                'decisions': stats.get('trading_decisions', 0),
                'positions': stats.get('positions', 0),
                'open_positions': open_positions,
                'account_state': stats.get('account_states', 0),
                'bot_status': stats.get('bot_status', 0)
            },
            'total_records': sum(stats.values()),
            'latest_timestamps': {
                'decision': None,  # TODO: query from trading_decisions
                'account_state': None  # TODO: query from account_states
            },
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        }), 500


@app.route('/api/database/reset', methods=['POST'])
def api_database_reset():
    """Reset database (WARNING: Deletes all data)."""
    from database import init_database
    import os

    try:
        # This is dangerous - require confirmation
        data = request.json or {}
        if not data.get('confirm'):
            return jsonify({'error': 'Reset requires confirmation'}), 400

        # Re-initialize database (creates tables if not exist)
        init_database()

        return jsonify({
            'success': True,
            'message': 'Database reset successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# BOT CONFIGURATION ENDPOINTS
# ============================================================================

@app.route('/api/bot_config', methods=['GET', 'POST'])
def api_bot_config():
    """Get or update bot configuration."""
    from database import get_connection

    if request.method == 'POST':
        data = request.json

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Update or insert config values
            for key, value in data.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO bot_config (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, str(value)))

            conn.commit()
            conn.close()

            return jsonify({'success': True, 'message': 'Configuration updated'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM bot_config")
            results = cursor.fetchall()
            conn.close()

            config_dict = {row[0]: row[1] for row in results}

            # Convert to structured config with proper types (all from database)
            structured_config = {
                # Trading parameters
                'min_margin_usd': float(config_dict.get('min_margin_usd', 20.0)),
                'max_margin_usd': float(config_dict.get('max_margin_usd', 200.0)),
                'min_balance_threshold': float(config_dict.get('min_balance_threshold', 10.0)),
                'execution_interval_seconds': int(config_dict.get('execution_interval_seconds', 300)),
                'max_open_positions': int(config_dict.get('max_open_positions', 3)),
                'trading_mode': config_dict.get('trading_mode', 'paper'),
                'max_position_size_usd': float(config_dict.get('max_position_size_usd', 500.0)),
                'max_leverage': int(config_dict.get('max_leverage', 5)),
                'trading_assets': config_dict.get('trading_assets', 'BTC,ETH,SOL'),
                'hyperliquid_testnet': config_dict.get('hyperliquid_testnet', 'true').lower() == 'true',

                # API keys status (don't expose actual keys, just whether they're configured)
                'has_hyperliquid_key': bool(config_dict.get('hyperliquid_wallet_private_key')),
                'has_anthropic_key': bool(config_dict.get('anthropic_api_key')),
            }

            return jsonify({
                'success': True,
                'config': structured_config,
                'note': 'Configuration loaded from database - changes apply on next bot restart'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# PROMPT PRESET ENDPOINTS
# ============================================================================

# Standard preset definitions
STANDARD_PRESETS = {
    'cooperative': {
        'name': 'Cooperative Trading',
        'description': 'Balanced risk approach with moderate position sizing and cooperative decision-making'
    },
    'hedging': {
        'name': 'Hedging Strategy',
        'description': 'Risk-averse approach focused on hedging positions and capital preservation'
    },
    'entry_exit': {
        'name': 'Entry/Exit Focus',
        'description': 'Tactical trading with emphasis on optimal entry and exit timing'
    },
    'date_collecting': {
        'name': 'Data Collection Mode',
        'description': 'Observation mode for collecting market data and analysis without trading'
    }
}

@app.route('/api/prompt_presets', methods=['GET', 'POST'])
def api_prompt_presets():
    """Get all prompt presets or create a new one."""
    from database import query_active_prompts, save_prompt, get_connection, save_strategy_preset, query_strategy_presets

    if request.method == 'POST':
        data = request.json
        required = ['name', 'prompt_type', 'prompt_text']

        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400

        try:
            # Save as a persistent preset
            preset_id = save_strategy_preset(
                name=data['name'],
                strategy_type=data['prompt_type'],
                prompt_text=data['prompt_text'],
                description=data.get('description')
            )
            
            # Also update the active prompt for this type, effectively "applying" it
            # This matches the "Apply & Save" behavior expected by the UI
            save_prompt(data['prompt_type'], data['prompt_text'])

            return jsonify({
                'success': True,
                'id': preset_id,
                'message': 'Preset saved and applied'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        try:
            # Get active preset name
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM bot_config WHERE key = 'active_preset'")
            result = cursor.fetchone()
            conn.close()
            active_preset = result[0] if result else 'cooperative'

            # Build list from standard presets
            presets_array = [
                {
                    'key': key,
                    'name': info['name'],
                    'description': info['description']
                }
                for key, info in STANDARD_PRESETS.items()
            ]
            
            # Add custom presets from database
            db_presets = query_strategy_presets()
            for p in db_presets:
                # Avoid duplicates if name matches standard key (though keys are different entities)
                # We use 'name' as key for custom presets in the UI logic usually
                presets_array.append({
                    'key': p['name'], # Use name as key for custom presets
                    'name': p['name'],
                    'description': p['description'] or f"Custom {p['strategy_type']} strategy",
                    'is_custom': True
                })

            return jsonify({
                'presets': presets_array,
                'active_preset': active_preset
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/prompt_presets/active', methods=['GET', 'POST'])
def api_prompt_presets_active():
    """Get or set the active prompt preset."""
    from database import get_connection

    if request.method == 'POST':
        data = request.json

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Store active preset name in bot_config
            cursor.execute("""
                INSERT OR REPLACE INTO bot_config (key, value)
                VALUES ('active_preset', ?)
            """, (data.get('preset_name', ''),))

            conn.commit()
            conn.close()

            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM bot_config WHERE key = 'active_preset'")
            result = cursor.fetchone()
            conn.close()

            active_preset = result[0] if result else None

            return jsonify({'active_preset': active_preset})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/prompt_presets/sample_user_prompt')
def api_sample_user_prompt():
    """Get a sample user prompt for testing."""
    sample_prompt = {
        'text': 'Sample user guidance prompt for testing the system.',
        'type': 'cycle'
    }
    return jsonify(sample_prompt)


@app.route('/api/prompt_presets/preview/<preset_key>')
def api_prompt_preset_preview(preset_key):
    """Get a preview of a specific preset's prompts."""
    
    try:
        from database import query_active_prompts, get_strategy_preset

        # Check if it is a standard preset
        if preset_key in STANDARD_PRESETS:
            # Get the prompts for this preset type
            prompts = query_active_prompts(preset_key)
            # Get the most recent prompt text (or use a default)
            system_prompt = prompts[0]['prompt_text'] if prompts else f'No {preset_key} prompt configured yet.'
            
            return jsonify({
                'preset_key': preset_key,
                'name': STANDARD_PRESETS[preset_key]['name'],
                'description': STANDARD_PRESETS[preset_key]['description'],
                'system_prompt': system_prompt,
                'user_prompt': '(Market data and context will be inserted here during trading)'
            })
            
        # Check if it is a custom preset from DB
        custom_preset = get_strategy_preset(preset_key)
        if custom_preset:
            return jsonify({
                'preset_key': custom_preset['name'],
                'name': custom_preset['name'],
                'description': custom_preset['description'] or f"Custom {custom_preset['strategy_type']} strategy",
                'system_prompt': custom_preset['prompt_text'],
                'user_prompt': '(Market data and context will be inserted here during trading)'
            })
            
        return jsonify({'error': 'Invalid preset key'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API INDEX
# ============================================================================

@app.route('/api/index')
def api_index():
    """API index - list all available endpoints."""
    endpoints = {
        "Health & Status": [
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check endpoint"
            },
            {
                "path": "/api/status",
                "method": "GET",
                "description": "Get bot status and configuration"
            }
        ],
        "Bot Control": [
            {
                "path": "/api/bot/start",
                "method": "POST",
                "description": "Start the trading bot"
            },
            {
                "path": "/api/bot/pause",
                "method": "POST",
                "description": "Pause the trading bot (keeps thread alive)"
            },
            {
                "path": "/api/bot/resume",
                "method": "POST",
                "description": "Resume the paused bot"
            },
            {
                "path": "/api/bot/stop",
                "method": "POST",
                "description": "Stop the trading bot completely"
            }
        ],
        "Market Data": [
            {
                "path": "/api/candles",
                "method": "GET/POST",
                "description": "Get or save OHLCV candle data"
            },
            {
                "path": "/api/indicators",
                "method": "GET/POST",
                "description": "Get or save TA indicators (SMA, EMA, MACD, RSI, FIB)"
            },
            {
                "path": "/api/market-data",
                "method": "GET/POST",
                "description": "Get or save market snapshots"
            },
            {
                "path": "/api/account-states",
                "method": "GET/POST",
                "description": "Get or save account state snapshots (balance, equity, PnL, margin)"
            }
        ],
        "Trading Data": [
            {
                "path": "/api/positions",
                "method": "GET/POST/PUT",
                "description": "Get, create, or update positions (POST creates position, PUT updates existing)"
            },
            {
                "path": "/api/decisions",
                "method": "GET/POST",
                "description": "Get or save trading decisions (GET supports asset filter and limit)"
            },
            {
                "path": "/api/visions",
                "method": "GET/POST",
                "description": "Get or save trading visions"
            }
        ],
        "Prompts": [
            {
                "path": "/api/prompts",
                "method": "GET/POST",
                "description": "Get or save strategy prompts (cooperative, hedging, entry_exit, date_collecting)"
            },
            {
                "path": "/api/prompt_presets",
                "method": "GET/POST",
                "description": "Get all prompt presets or create new preset"
            },
            {
                "path": "/api/prompt_presets/active",
                "method": "GET/POST",
                "description": "Get or set active prompt preset"
            },
            {
                "path": "/api/prompt_presets/sample_user_prompt",
                "method": "GET",
                "description": "Get sample user prompt for testing"
            }
        ],
        "Configuration": [
            {
                "path": "/api/bot_config",
                "method": "GET/POST",
                "description": "Get or update bot configuration"
            }
        ],
        "Database Management": [
            {
                "path": "/api/database/status",
                "method": "GET",
                "description": "Get database connection status and statistics"
            },
            {
                "path": "/api/database/reset",
                "method": "POST",
                "description": "Reset database (WARNING: deletes all data)"
            }
        ],
        "User Input / Commands": [
            {
                "path": "/api/user_input",
                "method": "GET",
                "description": "Get active user input"
            },
            {
                "path": "/api/user_input",
                "method": "POST",
                "description": "Send command to bot (cycle or interrupt)"
            },
            {
                "path": "/api/user_input",
                "method": "DELETE",
                "description": "Clear active user input"
            },
            {
                "path": "/api/upload_image",
                "method": "POST",
                "description": "Upload chart image for analysis"
            }
        ],
        "Documentation": [
            {
                "path": "/api/index",
                "method": "GET",
                "description": "This endpoint - API documentation"
            }
        ]
    }

    return jsonify({
        "version": "2.0.0",
        "name": "Motherhaven v2 API",
        "description": "Multi-user Hyperliquid trading bot API",
        "endpoints": endpoints,
        "total_endpoints": sum(len(category) for category in endpoints.values())
    })


if __name__ == '__main__':
    print("="*60)
    print("Motherhaven v2 - Trading Bot API")
    print("="*60)
    print(f"\nFlask server starting on port {settings.port}...")
    print(f"Bot will use {settings.execution_interval_seconds}s execution interval")
    print(f"Trading mode: {settings.trading_mode.upper()}")
    print(f"Trading assets: {', '.join(settings.get_trading_assets())}")
    print("\nWeb Interface:     http://localhost:5000/")
    print("API Documentation: http://localhost:5000/api/index")
    print("="*60)

    # Start the global bot instance
    if bot.state == BotState.STOPPED:
        bot.start()
        print(f"\n[BOT] Started in {bot.state.value.upper()} mode")

    app.run(host='0.0.0.0', port=settings.port, debug=settings.flask_debug)
