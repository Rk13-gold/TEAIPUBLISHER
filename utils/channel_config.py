"""
Multi-channel configuration management
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import sqlite3
from dataclasses import dataclass, asdict, field


@dataclass
class ChannelConfig:
    """Configuration for a single Telegram channel"""
    username: str
    title: str = ""
    channel_id: str = ""
    monitor_enabled: bool = True
    notification_enabled: bool = True
    update_interval: int = 30  # seconds
    last_message_id: int = 0
    subscriber_count: int = 0
    tags: List[str] = field(default_factory=list)
    custom_settings: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ChannelConfigManager:
    """Manager for multiple channel configurations"""
    
    def __init__(self, config_file: str = "channel_configs.json", db_file: str = "channels.db"):
        self.config_file = config_file
        self.db_file = db_file
        self.channels: Dict[str, ChannelConfig] = {}
        
        self._init_database()
        self.load_configurations()
    
    def _init_database(self):
        """Initialize SQLite database for channel configurations"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_configs (
                username TEXT PRIMARY KEY,
                title TEXT,
                channel_id TEXT,
                monitor_enabled BOOLEAN DEFAULT TRUE,
                notification_enabled BOOLEAN DEFAULT TRUE,
                update_interval INTEGER DEFAULT 30,
                last_message_id INTEGER DEFAULT 0,
                subscriber_count INTEGER DEFAULT 0,
                tags TEXT,  -- JSON array
                custom_settings TEXT,  -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                subscriber_count INTEGER,
                message_count INTEGER,
                engagement_rate REAL,
                activity_level TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES channel_configs (username)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                alert_type TEXT,
                message TEXT,
                severity TEXT DEFAULT 'info',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (username) REFERENCES channel_configs (username)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_channel(self, username: str, **kwargs) -> bool:
        """Add a new channel configuration"""
        if username in self.channels:
            return False
        
        config = ChannelConfig(username=username, **kwargs)
        self.channels[username] = config
        
        self._save_to_database(config)
        self.save_configurations()
        
        return True
    
    def update_channel(self, username: str, **kwargs) -> bool:
        """Update existing channel configuration"""
        if username not in self.channels:
            return False
        
        config = self.channels[username]
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.now().isoformat()
        
        self._save_to_database(config)
        self.save_configurations()
        
        return True
    
    def remove_channel(self, username: str) -> bool:
        """Remove a channel configuration"""
        if username not in self.channels:
            return False
        
        del self.channels[username]
        
        # Remove from database
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM channel_configs WHERE username = ?", (username,))
        cursor.execute("DELETE FROM channel_stats WHERE username = ?", (username,))
        cursor.execute("DELETE FROM channel_alerts WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        
        self.save_configurations()
        return True
    
    def get_channel(self, username: str) -> Optional[ChannelConfig]:
        """Get channel configuration"""
        return self.channels.get(username)
    
    def get_all_channels(self) -> Dict[str, ChannelConfig]:
        """Get all channel configurations"""
        return self.channels.copy()
    
    def get_monitored_channels(self) -> List[ChannelConfig]:
        """Get all channels with monitoring enabled"""
        return [config for config in self.channels.values() if config.monitor_enabled]
    
    def get_channels_by_tag(self, tag: str) -> List[ChannelConfig]:
        """Get channels by tag"""
        return [config for config in self.channels.values() if tag in config.tags]
    
    def add_tag(self, username: str, tag: str) -> bool:
        """Add tag to channel"""
        if username not in self.channels:
            return False
        
        config = self.channels[username]
        if tag not in config.tags:
            config.tags.append(tag)
            config.updated_at = datetime.now().isoformat()
            self._save_to_database(config)
            self.save_configurations()
        
        return True
    
    def remove_tag(self, username: str, tag: str) -> bool:
        """Remove tag from channel"""
        if username not in self.channels:
            return False
        
        config = self.channels[username]
        if tag in config.tags:
            config.tags.remove(tag)
            config.updated_at = datetime.now().isoformat()
            self._save_to_database(config)
            self.save_configurations()
        
        return True
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags"""
        all_tags = set()
        for config in self.channels.values():
            all_tags.update(config.tags)
        return sorted(list(all_tags))
    
    def record_stats(self, username: str, subscriber_count: int, message_count: int, 
                    engagement_rate: float, activity_level: str):
        """Record channel statistics"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO channel_stats 
            (username, subscriber_count, message_count, engagement_rate, activity_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, subscriber_count, message_count, engagement_rate, activity_level))
        
        conn.commit()
        conn.close()
        
        # Update channel config with latest subscriber count
        if username in self.channels:
            self.update_channel(username, subscriber_count=subscriber_count)
    
    def get_stats_history(self, username: str, days: int = 30) -> List[Dict]:
        """Get statistics history for a channel"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT subscriber_count, message_count, engagement_rate, activity_level, recorded_at
            FROM channel_stats
            WHERE username = ? AND recorded_at >= datetime('now', '-{} days')
            ORDER BY recorded_at DESC
        '''.format(days), (username,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "subscriber_count": row[0],
                "message_count": row[1],
                "engagement_rate": row[2],
                "activity_level": row[3],
                "recorded_at": row[4]
            })
        
        conn.close()
        return results
    
    def add_alert(self, username: str, alert_type: str, message: str, severity: str = "info"):
        """Add an alert for a channel"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO channel_alerts (username, alert_type, message, severity)
            VALUES (?, ?, ?, ?)
        ''', (username, alert_type, message, severity))
        
        conn.commit()
        conn.close()
    
    def get_alerts(self, username: str = None, unacknowledged_only: bool = True) -> List[Dict]:
        """Get alerts for channels"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, username, alert_type, message, severity, created_at, acknowledged
            FROM channel_alerts
        '''
        params = []
        
        conditions = []
        if username:
            conditions.append("username = ?")
            params.append(username)
        
        if unacknowledged_only:
            conditions.append("acknowledged = FALSE")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "username": row[1],
                "alert_type": row[2],
                "message": row[3],
                "severity": row[4],
                "created_at": row[5],
                "acknowledged": bool(row[6])
            })
        
        conn.close()
        return results
    
    def acknowledge_alert(self, alert_id: int):
        """Acknowledge an alert"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE channel_alerts SET acknowledged = TRUE WHERE id = ?
        ''', (alert_id,))
        
        conn.commit()
        conn.close()
    
    def bulk_update_monitoring(self, usernames: List[str], enabled: bool):
        """Bulk update monitoring status for multiple channels"""
        updated_count = 0
        for username in usernames:
            if self.update_channel(username, monitor_enabled=enabled):
                updated_count += 1
        return updated_count
    
    def export_configurations(self, file_path: str) -> bool:
        """Export configurations to file"""
        try:
            data = {
                "channels": {username: asdict(config) for username, config in self.channels.items()},
                "export_time": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def import_configurations(self, file_path: str) -> int:
        """Import configurations from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            channels_data = data.get("channels", {})
            
            for username, config_data in channels_data.items():
                # Remove username from config_data if present (to avoid duplication)
                config_data.pop("username", None)
                
                if self.add_channel(username, **config_data):
                    imported_count += 1
            
            return imported_count
        except Exception:
            return 0
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for all channels"""
        total_channels = len(self.channels)
        monitored_channels = len(self.get_monitored_channels())
        total_subscribers = sum(config.subscriber_count for config in self.channels.values())
        
        # Get recent alerts count
        recent_alerts = len(self.get_alerts(unacknowledged_only=True))
        
        return {
            "total_channels": total_channels,
            "monitored_channels": monitored_channels,
            "total_subscribers": total_subscribers,
            "unacknowledged_alerts": recent_alerts,
            "all_tags": self.get_all_tags()
        }
    
    def _save_to_database(self, config: ChannelConfig):
        """Save configuration to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO channel_configs 
            (username, title, channel_id, monitor_enabled, notification_enabled,
             update_interval, last_message_id, subscriber_count, tags, custom_settings,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            config.username, config.title, config.channel_id,
            config.monitor_enabled, config.notification_enabled,
            config.update_interval, config.last_message_id,
            config.subscriber_count, json.dumps(config.tags),
            json.dumps(config.custom_settings),
            config.created_at, config.updated_at
        ))
        
        conn.commit()
        conn.close()
    
    def load_configurations(self):
        """Load configurations from database and JSON file"""
        # First try to load from database
        self._load_from_database()
        
        # Then try to load from JSON file (for backup/migration)
        if os.path.exists(self.config_file):
            self._load_from_json()
    
    def _load_from_database(self):
        """Load configurations from database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM channel_configs')
            rows = cursor.fetchall()
            
            for row in rows:
                config = ChannelConfig(
                    username=row[0],
                    title=row[1] or "",
                    channel_id=row[2] or "",
                    monitor_enabled=bool(row[3]),
                    notification_enabled=bool(row[4]),
                    update_interval=row[5],
                    last_message_id=row[6],
                    subscriber_count=row[7],
                    tags=json.loads(row[8]) if row[8] else [],
                    custom_settings=json.loads(row[9]) if row[9] else {},
                    created_at=row[10] or datetime.now().isoformat(),
                    updated_at=row[11] or datetime.now().isoformat()
                )
                self.channels[config.username] = config
            
            conn.close()
        except Exception:
            pass  # Database might not exist yet
    
    def _load_from_json(self):
        """Load configurations from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            channels_data = data.get("channels", {})
            for username, config_data in channels_data.items():
                if username not in self.channels:  # Don't overwrite database data
                    config = ChannelConfig(**config_data)
                    self.channels[username] = config
        except Exception:
            pass  # File might not exist
    
    def save_configurations(self):
        """Save configurations to JSON file (for backup)"""
        try:
            data = {
                "channels": {username: asdict(config) for username, config in self.channels.items()},
                "last_saved": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Save might fail, but don't crash
