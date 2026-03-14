#!/usr/bin/env python3
"""
Database migration CLI tool

Usage:
    python -m scripts.migrate info              # Show current version
    python -m scripts.migrate history           # Show migration history
    python -m scripts.migrate up                # Migrate to latest
    python -m scripts.migrate down <version>    # Rollback to version
"""
import sys
import argparse
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database_manager import get_database_manager, DatabaseManager
from modules.settings import get_config


def main():
    parser = argparse.ArgumentParser(description='Database migration tool')
    parser.add_argument('command', choices=['info', 'history', 'up', 'down', 'check'],
                       help='Command to execute')
    parser.add_argument('target', nargs='?', help='Target version for down command')
    parser.add_argument('--db-path', help='Database path (default from config)')
    
    args = parser.parse_args()
    
    # Get database path
    if args.db_path:
        db_path = args.db_path
    else:
        config = get_config()
        db_path = config.database.path
    
    print(f"Using database: {db_path}")
    
    # Get database manager
    db = get_database_manager(db_path)
    
    if args.command == 'info':
        version = db.get_schema_version()
        print(f"Current schema version: {version}")
        print(f"Target schema version: {DatabaseManager.CURRENT_SCHEMA_VERSION}")
        if version < DatabaseManager.CURRENT_SCHEMA_VERSION:
            print(f"\u26A0\uFE0F  Database needs migration (run 'migrate up')")
        elif version > DatabaseManager.CURRENT_SCHEMA_VERSION:
            print(f"\u274C Database is newer than code version!")
        else:
            print(f"\u2713 Database is up to date")
    
    elif args.command == 'history':
        history = db.get_migration_history()
        print("\nMigration History:")
        print("-" * 70)
        for entry in history:
            print(f"Version {entry['version']}: {entry['description']}")
            print(f"  Applied: {entry['applied_at']}")
        print("-" * 70)
    
    elif args.command == 'up':
        current = db.get_schema_version()
        target = DatabaseManager.CURRENT_SCHEMA_VERSION
        if current < target:
            print(f"Migrating from version {current} to {target}...")
            # Re-initialize will run migrations
            db._initialize_schema()
            print("\u2713 Migration complete")
        else:
            print("\u2713 Already at latest version")
    
    elif args.command == 'down':
        print("\u274C Rollback not yet implemented")
        print("To rollback: restore database from backup")
    
    elif args.command == 'check':
        # Check schema integrity
        print("Checking schema integrity...")
        try:
            expected_tables = [
                'schema_version', 'action_log', 'economic_log', 'system_state',
                'hierarchy_of_needs', 'goals', 'goal_history',
                'discovered_capabilities', 'capability_validation',
                'reflection_log', 'effectiveness_metrics'
            ]
            
            results = db.query(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            existing_tables = [row['name'] for row in results]
            
            missing = set(expected_tables) - set(existing_tables)
            extra = set(existing_tables) - set(expected_tables) - {'sqlite_sequence'}
            
            if missing:
                print(f"\u274C Missing tables: {', '.join(missing)}")
            if extra:
                print(f"\u26A0\uFE0F  Extra tables: {', '.join(extra)}")
            if not missing and not extra:
                print("\u2713 All expected tables present")
            
            version = db.get_schema_version()
            if version == DatabaseManager.CURRENT_SCHEMA_VERSION:
                print(f"\u2713 Schema version correct ({version})")
            else:
                print(f"\u274C Schema version mismatch: {version} (expected {DatabaseManager.CURRENT_SCHEMA_VERSION})")
        
        except Exception as e:
            print(f"\u274C Schema check failed: {e}")


if __name__ == '__main__':
    main()
