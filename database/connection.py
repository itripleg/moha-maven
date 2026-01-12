"""
PostgreSQL connection pooling for Maven service.

Supports connecting to:
- maven_postgres (standalone mode)
- moha_postgres (integrated with moha-bot)
"""
import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Database configuration from environment
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'maven_data'),
    'user': os.getenv('DB_USER', 'maven_user'),
    'password': os.getenv('DB_PASSWORD', 'maven_password')
}

# Connection pool (1-10 connections)
_pool = None

def get_pool():
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                **DB_CONFIG
            )
            logger.info(f"Database pool created: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    return _pool

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM maven_memory")
            results = cursor.fetchall()
    """
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise e
    finally:
        pool.putconn(conn)

def query_maven_memory(limit=50):
    """
    Query Maven's memory from database.

    Returns:
        list: Recent memory entries
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT event_type, description, metadata, created_at
                FROM maven_memory
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cursor.fetchall()
            cursor.close()

            return [
                {
                    'event_type': row[0],
                    'description': row[1],
                    'metadata': row[2],
                    'created_at': row[3].isoformat() if row[3] else None
                }
                for row in rows
            ]
    except Exception as e:
        logger.warning(f"Could not query maven_memory (table may not exist): {e}")
        return []

def query_maven_decisions(limit=10):
    """
    Query Maven's recent decisions from database.

    Returns:
        list: Recent decision entries
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT decision_type, asset, action, reasoning, confidence, risk_level, created_at
                FROM maven_decisions
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cursor.fetchall()
            cursor.close()

            return [
                {
                    'decision_type': row[0],
                    'asset': row[1],
                    'action': row[2],
                    'reasoning': row[3],
                    'confidence': row[4],
                    'risk_level': row[5],
                    'created_at': row[6].isoformat() if row[6] else None
                }
                for row in rows
            ]
    except Exception as e:
        logger.warning(f"Could not query maven_decisions (table may not exist): {e}")
        return []

def query_maven_insights(limit=10):
    """
    Query Maven's market insights from database.

    Returns:
        list: Recent insight entries
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT insight_type, content, confidence, market_conditions, created_at
                FROM maven_insights
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cursor.fetchall()
            cursor.close()

            return [
                {
                    'insight_type': row[0],
                    'content': row[1],
                    'confidence': row[2],
                    'market_conditions': row[3],
                    'created_at': row[4].isoformat() if row[4] else None
                }
                for row in rows
            ]
    except Exception as e:
        logger.warning(f"Could not query maven_insights (table may not exist): {e}")
        return []

def test_connection():
    """Test database connection and return status."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            return {
                'connected': True,
                'host': DB_CONFIG['host'],
                'database': DB_CONFIG['database'],
                'version': version
            }
    except Exception as e:
        return {
            'connected': False,
            'error': str(e)
        }
