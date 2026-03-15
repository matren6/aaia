"""
Database Manager - Centralized database access and schema management

Provides a DatabaseManager with migration support for SQLite.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from threading import Lock, RLock
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and schema migrations"""

    CURRENT_SCHEMA_VERSION = 16

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None
        # Use reentrant lock to allow nested get_connection calls within same thread
        self._lock = RLock()

        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize or migrate schema
        self._initialize_schema()

    def _initialize_schema(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            ''')

            cursor.execute('SELECT MAX(version) FROM schema_version')
            result = cursor.fetchone()
            current_version = result[0] if result and result[0] else 0

            logger.info(f"Current schema version: {current_version}")

            if current_version < self.CURRENT_SCHEMA_VERSION:
                logger.info(f"Migrating from version {current_version} to {self.CURRENT_SCHEMA_VERSION}")
                self._run_migrations(current_version, self.CURRENT_SCHEMA_VERSION)
            elif current_version > self.CURRENT_SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database version {current_version} is newer than code version {self.CURRENT_SCHEMA_VERSION}."
                )

            conn.commit()

    def _run_migrations(self, from_version: int, to_version: int):
        from modules.migrations import get_migrations

        migrations = get_migrations()

        with self.get_connection() as conn:
            for version in range(from_version + 1, to_version + 1):
                if version not in migrations:
                    raise RuntimeError(f"Migration for version {version} not found")

                migration = migrations[version]
                logger.info(f"Applying migration {version}: {migration.description}")

                try:
                    migration.up(conn)
                    conn.execute(
                        'INSERT INTO schema_version (version, description) VALUES (?, ?)',
                        (version, migration.description)
                    )
                    conn.commit()
                    logger.info(f"Migration {version} completed")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Migration {version} failed: {e}")
                    raise RuntimeError(f"Migration {version} failed: {e}") from e

    @contextmanager
    def get_connection(self):
        with self._lock:
            if self._connection is None:
                self._connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
                self._connection.row_factory = sqlite3.Row

            yield self._connection

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor

    def executemany(self, sql: str, params_list: List[tuple]) -> sqlite3.Cursor:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()
            return cursor

    def query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()

    @contextmanager
    def transaction(self):
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None

    def get_schema_version(self) -> int:
        result = self.query_one('SELECT MAX(version) FROM schema_version')
        return result[0] if result and result[0] else 0

    def get_migration_history(self) -> List[Dict[str, Any]]:
        results = self.query('SELECT version, applied_at, description FROM schema_version ORDER BY version')
        return [dict(row) for row in results]


# Global instances - one per database path
_db_managers = {}
_db_manager_lock = Lock()

def get_database_manager(db_path: str = None) -> DatabaseManager:
    """Get or create database manager for given path."""
    if db_path is None:
        raise ValueError("db_path must be provided")

    # Normalize path
    db_path = str(Path(db_path).resolve())

    if db_path not in _db_managers:
        with _db_manager_lock:
            if db_path not in _db_managers:
                _db_managers[db_path] = DatabaseManager(db_path)

    return _db_managers[db_path]

def reset_database_manager(db_path: str = None):
    """Reset database manager for given path or all."""
    with _db_manager_lock:
        if db_path:
            db_path = str(Path(db_path).resolve())
            if db_path in _db_managers:
                _db_managers[db_path].close()
                del _db_managers[db_path]
        else:
            # Reset all
            for mgr in _db_managers.values():
                mgr.close()
            _db_managers.clear()

