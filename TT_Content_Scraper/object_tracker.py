import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging
import os
import json


class ObjectStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"
    RETRY = "retry"

class ObjectTracker:
    """Create a JSON file that tracks, wether an object (like a video id) was already processed or caused an error etc."""
    def __init__(self, state_file="object_progress.json"):
        self.state_file = state_file
        self.load_state()
    
    def load_state(self):
        """Load existing state or create new one"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "objects": {},
                "last_updated": None,
                "stats": {"completed": 0, "errors": 0, "pending": 0}
            }
    
    def save_state(self):
        """Save current state to file"""
        self.state["last_updated"] = datetime.now().isoformat()
        self._update_stats()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def add_object(self, id, title=None):
        """Add a new object to track"""
        self.state["objects"][id] = {
            "status": ObjectStatus.PENDING.value,
            "title": title,
            "added_at": datetime.now().isoformat(),
            "attempts": 0,
            "last_error": None,
            "completed_at": None
        }
        self.save_state()
    
    def add_objects(self, ids, title=None):
        """Add a new object to track"""
        for id in ids:
            self.state["objects"][id] = {
                "status": ObjectStatus.PENDING.value,
                "title": title,
                "added_at": datetime.now().isoformat(),
                "attempts": 0,
                "last_error": None,
                "completed_at": None
            }
        self.save_state()

    def mark_completed(self, id, file_path=None):
        """Mark object as successfully downloaded"""
        if id in self.state["objects"]:
            self.state["objects"][id].update({
                "status": ObjectStatus.COMPLETED.value,
                "completed_at": datetime.now().isoformat(),
                "file_path": file_path
            })
            self.save_state()

    def mark_completed_multi(self, ids, file_paths=None):
        """Mark object as successfully downloaded"""

        for i in range(len(ids)):
            id = ids[i]
            if file_paths:
                file_path = file_paths[i]
            else:
                file_path = None

            if id in self.state["objects"]:
                self.state["objects"][id].update({
                    "status": ObjectStatus.COMPLETED.value,
                    "completed_at": datetime.now().isoformat(),
                    "file_path": file_path
                })
            
        self.save_state()
    
    def mark_error(self, id, error_message):
        """Mark object as error, with retry logic"""
        if id in self.state["objects"]:
            object = self.state["objects"][id]
            object["attempts"] += 1
            object["last_error"] = error_message
            object["last_attempt"] = datetime.now().isoformat()
            
            object["status"] = ObjectStatus.ERROR.value

            #if object["attempts"] >= max_retries:
            #    object["status"] = ObjectStatus.ERROR.value
            #else:
            #    object["status"] = ObjectStatus.RETRY.value
            
            self.save_state()
    
    def get_pending_objects(self) -> list[object]:
        """Get all objects that need to be processed"""
        return [id for id, data in self.state["objects"].items() 
                if data["status"] in [ObjectStatus.PENDING.value, ObjectStatus.RETRY.value]]
    
    def get_error_objects(self):
        """Get all objects that failed"""
        return {id: data for id, data in self.state["objects"].items() 
                if data["status"] == ObjectStatus.ERROR.value}
    
    def get_completed_objects(self):
        """Get all successfully downloaded objects"""
        return {id: data for id, data in self.state["objects"].items() 
                if data["status"] == ObjectStatus.COMPLETED.value}
    
    def get_stats(self):
        """Get the statistics"""
        return self.state["stats"]

    
    def _update_stats(self):
        """Update statistics"""
        stats = {"completed": 0, "errors": 0, "pending": 0, "retry": 0}
        for data in self.state["objects"].values():
            status = data["status"]
            if status in stats:
                stats[status] += 1
            elif status == ObjectStatus.RETRY.value:
                stats["pending"] += 1
        self.state["stats"] = stats