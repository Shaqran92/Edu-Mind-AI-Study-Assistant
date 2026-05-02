# core/migrations.py
"""
Data Migration Script: JSON -> SQLite.
"""

import json
import os
from typing import List, Dict

from core.db import get_db
from utils.logger import get_logger

logger = get_logger("migrations")

USERS_FILE = "users.json"

def migrate_users_to_db():
    """Migrate users.json to SQLite."""
    if not os.path.exists(USERS_FILE):
        return

    db = get_db()
    
    try:
        with open(USERS_FILE, 'r') as f:
            raw_data = json.load(f)
        
        # Handle both formats: {"users": [...]} and [...]
        if isinstance(raw_data, dict) and "users" in raw_data:
            users_data = raw_data["users"]
        elif isinstance(raw_data, list):
            users_data = raw_data
        else:
            logger.warning("users.json has unexpected format, skipping migration")
            return

        count = 0
        with db.get_cursor() as cursor:
            for user in users_data:
                if not isinstance(user, dict):
                    continue
                    
                # Check if exists
                cursor.execute("SELECT 1 FROM users WHERE id = ?", (user.get('id', ''),))
                if cursor.fetchone():
                    continue
                
                # Insert User
                cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, salt, created_at, avatar_url, is_guest)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.get('id', ''), 
                    user.get('username', ''), 
                    user.get('email', ''), 
                    user.get('password_hash', ''), 
                    user.get('salt', ''), 
                    user.get('created_at', ''),
                    user.get('avatar_url', ''),
                    0
                ))
                
                # Insert Profile (Default)
                cursor.execute("""
                INSERT OR IGNORE INTO profiles (user_id, display_name)
                VALUES (?, ?)
                """, (user.get('id', ''), user.get('username', '')))
                
                count += 1
                
        if count > 0:
            logger.info(f"Migrated {count} users to database.")
            os.rename(USERS_FILE, USERS_FILE + ".bak")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")

def run_migrations():
    """Run all migrations."""
    print("[EduMind] Checking for data migrations...")
    migrate_users_to_db()
