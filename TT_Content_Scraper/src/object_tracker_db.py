import sqlite3
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional

import TT_Content_Scraper.src.logger
logger = logging.getLogger('TTCS.ObjTracker')

class ObjectStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"
    RETRY = "retry"


class ObjectTracker:
    """Create an SQLite database that tracks whether an object (like a video id) was already processed or caused an error etc."""
    
    def __init__(self, db_file="object_progress.db"):

        if db_file is not None:
            self.db_file = db_file
            self.conn = None
            self._connect()
            self._create_tables()
            self._create_indexes()
    
    def _connect(self):
        """Establish connection to SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            # Enable foreign keys and set pragmas for better performance
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")  # Better concurrent access
            self.conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes
            logger.info(f"Connected to SQLite database: {self.db_file}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def _create_tables(self):
        """Create the necessary tables if they don't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS objects (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            title TEXT,
            type TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            attempts INTEGER DEFAULT 0,
            last_error TEXT,
            last_attempt TIMESTAMP,
            file_path TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create metadata table for storing last_updated and other global info
        create_metadata_sql = """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create trigger to update the updated_at timestamp
        create_trigger_sql = """
        CREATE TRIGGER IF NOT EXISTS update_timestamp 
        AFTER UPDATE ON objects
        BEGIN
            UPDATE objects SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = NEW.id;
        END;
        """
        
        try:
            self.conn.execute(create_table_sql)
            self.conn.execute(create_metadata_sql)
            self.conn.execute(create_trigger_sql)
            self.conn.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for better query performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_status ON objects(status)",
            "CREATE INDEX IF NOT EXISTS idx_added_at ON objects(added_at)",
            "CREATE INDEX IF NOT EXISTS idx_completed_at ON objects(completed_at)",
        ]
        
        try:
            for index_sql in indexes:
                self.conn.execute(index_sql)
            self.conn.commit()
            logger.info("Database indexes created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating indexes: {e}")
            raise
    
    def _update_metadata(self, key: str, value: str):
        """Update metadata table."""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at) 
                VALUES (?, ?, ?)
            """, (key, value, datetime.now().isoformat()))
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error updating metadata: {e}")
            raise
            
    def add_object(self, id: str, title: Optional[str] = None, type: Optional[str] = None):
        """Add a new object to track"""
        try:
            self.conn.execute("""
                INSERT OR IGNORE INTO objects 
                (id, status, title, type, added_at, attempts) 
                VALUES (?, ?, ?, ?, ?, 0)
            """, (id, ObjectStatus.PENDING.value, title, type, datetime.now().isoformat()))
            self.conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Error adding object {id}: {e}")
            raise
    
    def add_objects(self, ids: List[str], title: Optional[str] = None, type: Optional[str] = None):
        """Add multiple objects to track"""
        try:
            current_time = datetime.now().isoformat()
            objects_data = [
                (id, ObjectStatus.PENDING.value, title, type, current_time, 0) 
                for id in ids
            ]
            
            self.conn.executemany("""
                INSERT OR IGNORE INTO objects 
                (id, status, title, type, added_at, attempts) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, objects_data)
            self.conn.commit()
            
            logger.info(f"Added {len(ids)} objects to tracker")
        except sqlite3.Error as e:
            logger.error(f"Error adding objects: {e}")
            raise
    
    def mark_completed(self, id: str, file_path: Optional[str] = None):
        """Mark object as successfully completed"""
        try:
            self.conn.execute("""
                UPDATE objects 
                SET status = ?, completed_at = ?, file_path = ?
                WHERE id = ?
            """, (ObjectStatus.COMPLETED.value, datetime.now().isoformat(), file_path, id))
            self.conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Error marking object {id} as completed: {e}")
            raise
    
    def mark_completed_multi(self, ids: List[str], file_paths: Optional[List[str]] = None):
        """Mark multiple objects as successfully completed"""
        try:
            current_time = datetime.now().isoformat()
            
            if file_paths:
                # With file paths
                update_data = [
                    (ObjectStatus.COMPLETED.value, current_time, file_paths[i], ids[i])
                    for i in range(len(ids))
                ]
            else:
                # Without file paths
                update_data = [
                    (ObjectStatus.COMPLETED.value, current_time, None, id)
                    for id in ids
                ]
            
            self.conn.executemany("""
                UPDATE objects 
                SET status = ?, completed_at = ?, file_path = ?
                WHERE id = ?
            """, update_data)
            self.conn.commit()
            
            logger.info(f"Marked {len(ids)} objects as completed")
        except sqlite3.Error as e:
            logger.error(f"Error marking objects as completed: {e}")
            raise
    
    def mark_error(self, id: str, error_message: str):
        """Mark object as error"""
        try:
            current_time = datetime.now().isoformat()
            
            # Get current attempts count
            cursor = self.conn.execute(
                "SELECT attempts FROM objects WHERE id = ?", (id,)
            )
            result = cursor.fetchone()
            attempts = (result[0] + 1) if result else 1
            
            self.conn.execute("""
                UPDATE objects 
                SET status = ?, attempts = ?, last_error = ?, last_attempt = ?
                WHERE id = ?
            """, (ObjectStatus.ERROR.value, attempts, error_message, current_time, id))
            self.conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Error marking object {id} as error: {e}")
            raise
    
    def get_pending_objects(self, type="all", limit:int=10**10) -> List[str]:
        """Get all objects that need to be processed"""
        try:
            if type == "all":
                cursor = self.conn.execute("""
                    SELECT id, title, type 
                    FROM objects 
                    WHERE status IN (?, ?)
                    LIMIT ? 
                """, (ObjectStatus.PENDING.value, ObjectStatus.RETRY.value, limit))
            else:
                cursor = self.conn.execute("""
                    SELECT id, title, type 
                    FROM objects 
                    WHERE status IN (?, ?) AND type = ?
                    LIMIT ? 
                """, (ObjectStatus.PENDING.value, ObjectStatus.RETRY.value, type, limit))

            result = {}
            for row in cursor.fetchall():
                result[row[0]] = {
                    "title":row[1],
                    "type": row[2]
                }
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting pending objects: {e}")
            raise
    
    def get_error_objects(self) -> Dict[str, Dict[str, Any]]:
        """Get all objects that failed"""
        try:
            cursor = self.conn.execute("""
                SELECT id, title, type, added_at, attempts, last_error, last_attempt, file_path
                FROM objects 
                WHERE status = ?
                ORDER BY last_attempt DESC
            """, (ObjectStatus.ERROR.value,))
            
            result = {}
            for row in cursor.fetchall():
                result[row[0]] = {
                    "status": ObjectStatus.ERROR.value,
                    "title": row[1],
                    "type": row[2],
                    "added_at": row[3],
                    "attempts": row[4],
                    "last_error": row[5],
                    "last_attempt": row[6],
                    "file_path": row[7],
                    "completed_at": None
                }
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting error objects: {e}")
            raise
    
    def get_completed_objects(self) -> Dict[str, Dict[str, Any]]:
        """Get all successfully completed objects"""
        try:
            cursor = self.conn.execute("""
                SELECT id, title, type, added_at, completed_at, attempts, file_path
                FROM objects 
                WHERE status = ?
                ORDER BY completed_at DESC
            """, (ObjectStatus.COMPLETED.value,))
            
            result = {}
            for row in cursor.fetchall():
                result[row[0]] = {
                    "status": ObjectStatus.COMPLETED.value,
                    "title": row[1],
                    "type": row[2],
                    "added_at": row[3],
                    "completed_at": row[4],
                    "attempts": row[5],
                    "last_error": None,
                    "file_path": row[6]
                }
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting completed objects: {e}")
            raise
    
    def get_stats(self, type="all") -> Dict[str, int]:
        """Get processing statistics"""
        try:
            if type == "all":
                cursor = self.conn.execute("""
                    SELECT status, COUNT(*) 
                    FROM objects 
                    GROUP BY status
                """)
            else:
                cursor = self.conn.execute("""
                    SELECT status, COUNT(*) 
                    FROM objects 
                    WHERE type = ?
                    GROUP BY status
                """, (type,))
            
            stats = {"completed": 0, "errors": 0, "pending": 0, "retry": 0}
            for status, count in cursor.fetchall():
                if status == ObjectStatus.COMPLETED.value:
                    stats["completed"] = count
                elif status == ObjectStatus.ERROR.value:
                    stats["errors"] = count
                elif status == ObjectStatus.PENDING.value:
                    stats["pending"] = count
                elif status == ObjectStatus.RETRY.value:
                    stats["retry"] = count
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}")
            raise
    
    def get_object_status(self, id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific object"""
        try:
            cursor = self.conn.execute("""
                SELECT status, title, type, added_at, completed_at, attempts, last_error, last_attempt, file_path
                FROM objects 
                WHERE id = ?
            """, (id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "status": result[0],
                    "title": result[1],
                    "type": result[2],
                    "added_at": result[3],
                    "completed_at": result[4],
                    "attempts": result[5],
                    "last_error": result[6],
                    "last_attempt": result[7],
                    "file_path": result[8]
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting object status for {id}: {e}")
            raise
    
    def is_completed(self, id: str) -> bool:
        """Check if an object is completed"""
        try:
            cursor = self.conn.execute(
                "SELECT 1 FROM objects WHERE id = ? AND status = ?",
                (id, ObjectStatus.COMPLETED.value)
            )
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking if object {id} is completed: {e}")
            raise
    
    def reset_errors_to_pending(self):
        """Reset all error objects back to pending for retry"""
        try:
            cursor = self.conn.execute("""
                UPDATE objects 
                SET status = ?, last_error = NULL, last_attempt = NULL
                WHERE status = ?
            """, (ObjectStatus.PENDING.value, ObjectStatus.ERROR.value))
            self.conn.commit()
            
            logger.info(f"Reset {cursor.rowcount} error objects to pending")
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error resetting error objects: {e}")
            raise
    
    def reset_all_to_pending(self):
        """Reset all objects back to pending for retry"""
        try:
            cursor = self.conn.execute("""
                UPDATE objects 
                SET status = "pending", last_error = NULL, last_attempt = NULL
            """)
            self.conn.commit()
            
            logger.info(f"Reset {cursor.rowcount} objects to pending")
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error resetting error objects: {e}")
            raise
    
    def clear_all_data(self):
        """Clear all tracking data (use with caution!)"""
        try:
            self.conn.execute("DELETE FROM objects")
            self.conn.execute("DELETE FROM metadata")
            self.conn.commit()
            logger.info("All tracking data cleared")
        except sqlite3.Error as e:
            logger.error(f"Error clearing all data: {e}")
            raise
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()