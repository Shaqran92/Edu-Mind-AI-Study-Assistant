# core/sync.py
"""
Cloud synchronization service for EduMind.
Simulates syncing local JSON data to a remote cloud provider.
"""

import json
import time
import os
from datetime import datetime
from threading import Thread
from typing import Callable, Optional

from utils.logger import get_logger

logger = get_logger("cloud_sync")

class CloudSyncService:
    """
    Handles syncing of user data to cloud.
    Currently implements a local backup simulation that works like a sync.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.local_dir = f"user_data/{user_id}"
        self.last_sync = None
        self.is_syncing = False

    def sync_now(self, callback: Optional[Callable[[bool, str], None]] = None):
        """
        Trigger a sync operation.
        """
        if self.is_syncing:
            return
        
        self.is_syncing = True
        
        # Run in thread
        t = Thread(target=self._perform_sync, args=(callback,))
        t.start()

    def _perform_sync(self, callback):
        try:
            logger.info(f"Starting cloud sync for {self.user_id}")
            time.sleep(2) # Simulate network delay
            
            # Here we would upload files to Firebase/AWS
            # user_progress.json, study_goals.json, notes/, etc.
            
            # For now, we update the timestamp
            self.last_sync = datetime.now()
            logger.info("Sync completed successfully")
            
            if callback:
                callback(True, "Sync complete!")
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            if callback:
                callback(False, str(e))
        finally:
            self.is_syncing = False

    def get_status(self) -> str:
        if self.is_syncing:
            return "Syncing..."
        if self.last_sync:
            return f"Last synced: {self.last_sync.strftime('%H:%M')}"
        return "Not synced"
