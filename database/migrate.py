#!/usr/bin/env python3
"""
Maven Database Migration Script

Initializes or updates the maven_postgres database with all required schemas.
Idempotent - safe to run multiple times.

Usage:
    python database/migrate.py
    python database/migrate.py --schema financial  # Run specific schema only
"""
import os
import sys
import logging
from pathlib import Path
import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database config from environment
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'maven_postgres'),
    'port': int(os.getenv('DB_PORT', 5433)),
    'database': os.getenv('DB_NAME', 'maven_data'),
    'user': os.getenv('DB_USER', 'maven_user'),
    'password': os.getenv('DB_PASSWORD', 'maven_password')
}

# Schema files
SCHEMAS_DIR = Path(__file__).parent / 'schemas'
SCHEMA_FILES = {
    'conversations': SCHEMAS_DIR / 'maven_conversations.sql',
    'financial': SCHEMAS_DIR / 'maven_financial.sql'
}


def get_db_connection():
    """Create a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"Connected to {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def run_schema_file(conn, schema_name, schema_file):
    """
    Execute a schema SQL file.

    Args:
        conn: Database connection
        schema_name: Name of the schema (for logging)
        schema_file: Path to SQL file
    """
    try:
        logger.info(f"Running {schema_name} schema: {schema_file.name}")

        # Read SQL file
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Execute SQL
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()

        logger.info(f"✓ {schema_name} schema applied successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to apply {schema_name} schema: {e}")
        conn.rollback()
        return False


def verify_tables(conn):
    """Verify that all expected tables exist."""
    expected_tables = [
        'maven_conversations',
        'maven_decisions',
        'maven_trades',
        'maven_portfolio_snapshots',
        'maven_performance_metrics',
        'maven_insights',
        'maven_memory'
    ]

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        existing_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()

        logger.info(f"Found {len(existing_tables)} tables in database")

        # Check for expected tables
        missing = []
        for table in expected_tables:
            if table in existing_tables:
                logger.info(f"  ✓ {table}")
            else:
                logger.warning(f"  ✗ {table} - MISSING")
                missing.append(table)

        if missing:
            logger.warning(f"Missing tables: {', '.join(missing)}")
            return False

        logger.info("All expected tables exist!")
        return True

    except Exception as e:
        logger.error(f"Failed to verify tables: {e}")
        return False


def get_table_counts(conn):
    """Get row counts for all tables."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name LIKE 'maven_%'
            ORDER BY table_name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        logger.info("\nTable row counts:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count} rows")

        cursor.close()

    except Exception as e:
        logger.error(f"Failed to get table counts: {e}")


def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description='Maven Database Migration')
    parser.add_argument(
        '--schema',
        choices=['conversations', 'financial', 'all'],
        default='all',
        help='Which schema to run (default: all)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify tables, do not run migrations'
    )
    parser.add_argument(
        '--counts',
        action='store_true',
        help='Show table row counts after migration'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Maven Database Migration")
    logger.info("=" * 60)

    # Connect to database
    try:
        conn = get_db_connection()
    except Exception as e:
        logger.error(f"Cannot proceed without database connection")
        return 1

    try:
        # Verify only mode
        if args.verify_only:
            verify_tables(conn)
            if args.counts:
                get_table_counts(conn)
            return 0

        # Run migrations
        success = True

        if args.schema in ['conversations', 'all']:
            if not run_schema_file(conn, 'conversations', SCHEMA_FILES['conversations']):
                success = False

        if args.schema in ['financial', 'all']:
            if not run_schema_file(conn, 'financial', SCHEMA_FILES['financial']):
                success = False

        # Verify tables exist
        logger.info("\n" + "=" * 60)
        logger.info("Verifying database state")
        logger.info("=" * 60)
        verify_tables(conn)

        # Show counts if requested
        if args.counts:
            get_table_counts(conn)

        if success:
            logger.info("\n✓ Migration completed successfully!")
            return 0
        else:
            logger.error("\n✗ Migration completed with errors")
            return 1

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1

    finally:
        conn.close()
        logger.info("Database connection closed")


if __name__ == '__main__':
    sys.exit(main())
