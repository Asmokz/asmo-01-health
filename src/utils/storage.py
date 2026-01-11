"""
Storage utility for managing health history JSON file
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class HealthStorage:
    """Manages the health history JSON storage with automatic cleanup"""
    
    def __init__(self, history_file: str, retention_days: int = 7):
        """
        Initialize storage manager
        
        Args:
            history_file: Path to the JSON history file
            retention_days: Number of days to keep history
        """
        self.history_file = Path(history_file)
        self.retention_days = retention_days
        
        # Ensure directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty file if doesn't exist
        if not self.history_file.exists():
            self._write_history([])
    
    def load_history(self) -> List[Dict]:
        """
        Load all history entries from file
        
        Returns:
            List of history entries
        """
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_history(self, data: List[Dict]) -> None:
        """Write history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_entry(self, entry: Dict) -> None:
        """
        Add a new entry to history
        
        Args:
            entry: Dictionary containing health metrics
        """
        # Ensure timestamp exists
        if 'timestamp' not in entry:
            entry['timestamp'] = datetime.now().isoformat()
        
        # Load current history
        history = self.load_history()
        
        # Add new entry
        history.append(entry)
        
        # Cleanup old entries
        history = self._cleanup_old_entries(history)
        
        # Save
        self._write_history(history)
    
    def _cleanup_old_entries(self, history: List[Dict]) -> List[Dict]:
        """
        Remove entries older than retention_days
        
        Args:
            history: List of history entries
            
        Returns:
            Filtered list
        """
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        filtered = []
        for entry in history:
            try:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time >= cutoff:
                    filtered.append(entry)
            except (KeyError, ValueError):
                # Keep entries without valid timestamp (better safe than sorry)
                filtered.append(entry)
        
        return filtered
    
    def get_last_24h(self) -> List[Dict]:
        """
        Get all entries from the last 24 hours
        
        Returns:
            List of entries from last 24h
        """
        history = self.load_history()
        cutoff = datetime.now() - timedelta(hours=24)
        
        filtered = []
        for entry in history:
            try:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time >= cutoff:
                    filtered.append(entry)
            except (KeyError, ValueError):
                continue
        
        return filtered
    
    def get_entries_between(self, start: datetime, end: datetime) -> List[Dict]:
        """
        Get entries between two timestamps
        
        Args:
            start: Start datetime
            end: End datetime
            
        Returns:
            List of entries in range
        """
        history = self.load_history()
        
        filtered = []
        for entry in history:
            try:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if start <= entry_time <= end:
                    filtered.append(entry)
            except (KeyError, ValueError):
                continue
        
        return filtered
    
    def get_latest_entry(self) -> Optional[Dict]:
        """
        Get the most recent entry
        
        Returns:
            Latest entry or None if empty
        """
        history = self.load_history()
        return history[-1] if history else None
    
    def get_file_size_mb(self) -> float:
        """
        Get the size of the history file in MB
        
        Returns:
            File size in megabytes
        """
        if self.history_file.exists():
            return self.history_file.stat().st_size / (1024 * 1024)
        return 0.0
