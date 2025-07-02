"""
Enhanced Telegram Client with caching, batch operations, and real-time updates
"""
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Union
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from telethon.errors import SessionPasswordNeededError, FloodWaitError
import json
import sqlite3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TelegramEntityCache:
    """Cache system for Telegram entities to improve performance"""
    
    def __init__(self, cache_duration: int = 3600):  # 1 hour default
        self.cache_duration = cache_duration
        self.cache: Dict[str, Dict] = {}
        self.last_updated: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached entity if not expired"""
        if key not in self.cache:
            return None
            
        if time.time() - self.last_updated.get(key, 0) > self.cache_duration:
            self.invalidate(key)
            return None
            
        return self.cache[key]
    
    def set(self, key: str, value: Dict):
        """Cache entity with timestamp"""
        self.cache[key] = value
        self.last_updated[key] = time.time()
    
    def invalidate(self, key: str):
        """Remove cached entity"""
        self.cache.pop(key, None)
        self.last_updated.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.last_updated.clear()


class EnhancedTelegramClient:
    """Enhanced Telegram client with caching, batch operations, and error handling"""
    
    def __init__(self, session_name: str, api_id: int, api_hash: str, cache_duration: int = 3600):
        self.session_name = session_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = None
        self.cache = TelegramEntityCache(cache_duration)
        self.is_connected = False
        self._connection_lock = asyncio.Lock()
        
        # Database for persistent storage
        self.db_path = "telegram_cache.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for persistent caching"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_cache (
                identifier TEXT PRIMARY KEY,
                entity_data TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscribers INTEGER,
                title TEXT,
                username TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                results TEXT,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def connect(self) -> bool:
        """Connect to Telegram with proper error handling"""
        async with self._connection_lock:
            if self.is_connected and self.client:
                return True
                
            try:
                self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
                await self.client.start()
                self.is_connected = True
                logger.info("Successfully connected to Telegram")
                return True
                
            except SessionPasswordNeededError:
                logger.error("Two-factor authentication required")
                return False
            except Exception as e:
                logger.error(f"Failed to connect to Telegram: {e}")
                return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
    
    async def get_entity_info(self, identifier: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get entity information with caching
        
        Args:
            identifier: Username, phone number, or entity ID
            force_refresh: Force refresh cache
            
        Returns:
            Dictionary with entity information or None if not found
        """
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = self.cache.get(identifier)
            if cached:
                return cached
            
            # Check database cache
            db_cached = self._get_from_db_cache(identifier)
            if db_cached:
                self.cache.set(identifier, db_cached)
                return db_cached
        
        # Connect if needed
        if not await self.connect():
            return None
        
        try:
            # Handle different identifier types
            if identifier.startswith('@'):
                identifier = identifier[1:]  # Remove @ prefix
            
            # Get entity with retry logic
            entity = await self._get_entity_with_retry(identifier)
            if not entity:
                return None
            
            # Extract information
            info = await self._extract_entity_info(entity)
            
            # Cache the result
            self.cache.set(identifier, info)
            self._save_to_db_cache(identifier, info)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting entity info for {identifier}: {e}")
            return None
    
    async def _get_entity_with_retry(self, identifier: str, max_retries: int = 3):
        """Get entity with retry logic for handling FloodWait errors"""
        for attempt in range(max_retries):
            try:
                return await self.client.get_entity(identifier)
            except FloodWaitError as e:
                if attempt < max_retries - 1:
                    wait_time = min(e.seconds, 300)  # Max 5 minutes
                    logger.warning(f"FloodWait error, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        return None
    
    async def _extract_entity_info(self, entity) -> Dict:
        """Extract relevant information from Telegram entity"""
        info = {
            "id": entity.id,
            "type": "unknown",
            "title": getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown')),
            "username": getattr(entity, 'username', None),
            "last_updated": datetime.now().isoformat()
        }
        
        if hasattr(entity, 'participants_count'):
            info["subscribers"] = entity.participants_count
            info["type"] = "channel" if hasattr(entity, 'broadcast') and entity.broadcast else "group"
        elif hasattr(entity, 'first_name'):
            info["type"] = "user"
        
        # Additional information for channels/groups
        if hasattr(entity, 'about'):
            info["about"] = entity.about
        
        if hasattr(entity, 'date'):
            info["created_date"] = entity.date.isoformat()
        
        return info
    
    async def batch_get_entities(self, identifiers: List[str], max_concurrent: int = 5) -> Dict[str, Optional[Dict]]:
        """
        Get multiple entities in batch with concurrency control
        
        Args:
            identifiers: List of usernames, phone numbers, or entity IDs
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dictionary mapping identifier to entity info
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def get_single(identifier: str) -> Tuple[str, Optional[Dict]]:
            async with semaphore:
                info = await self.get_entity_info(identifier)
                return identifier, info
        
        tasks = [get_single(identifier) for identifier in identifiers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch operation error: {result}")
                continue
            identifier, info = result
            output[identifier] = info
        
        return output
    
    async def search_channels(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for channels/groups by name or description
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        if not await self.connect():
            return []
        
        try:
            # Search using Telegram's search functionality
            search_result = await self.client.get_dialogs(limit=limit)
            
            results = []
            query_lower = query.lower()
            
            for dialog in search_result:
                entity = dialog.entity
                title = getattr(entity, 'title', getattr(entity, 'first_name', ''))
                username = getattr(entity, 'username', '')
                
                # Check if query matches title or username
                if (query_lower in title.lower() or 
                    (username and query_lower in username.lower())):
                    
                    info = await self._extract_entity_info(entity)
                    results.append(info)
            
            # Save search to history
            self._save_search_history(query, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching channels: {e}")
            return []
    
    async def get_recent_messages(self, identifier: str, limit: int = 10) -> List[Dict]:
        """Get recent messages from a channel/group with enhanced information"""
        if not await self.connect():
            return []
        
        try:
            entity = await self.client.get_entity(identifier)
            messages = []
            
            async for message in self.client.iter_messages(entity, limit=limit):
                msg_info = {
                    "id": message.id,
                    "text": message.text or "",
                    "date": message.date.isoformat() if message.date else None,
                    "views": getattr(message, 'views', 0),
                    "forwards": getattr(message, 'forwards', 0),
                    "replies": getattr(message.replies, 'replies', 0) if message.replies else 0,
                    "reactions_count": 0,
                    "media_type": None
                }
                
                # Count reactions
                if message.reactions:
                    msg_info["reactions_count"] = sum(r.count for r in message.reactions.results)
                
                # Detect media type
                if message.media:
                    if hasattr(message.media, 'photo'):
                        msg_info["media_type"] = "photo"
                    elif hasattr(message.media, 'document'):
                        msg_info["media_type"] = "document"
                    elif hasattr(message.media, 'video'):
                        msg_info["media_type"] = "video"
                
                messages.append(msg_info)
            
            return messages
            
        except Exception as e:
            # Check if this is the common bot restriction error
            if "GetHistoryRequest" in str(e) and "bot users is restricted" in str(e):
                logger.warning(f"Bot API restriction - cannot fetch message history for {identifier}. This is normal for bot tokens.")
                return []
            else:
                logger.error(f"Error getting recent messages: {e}")
            return []
    
    def _get_from_db_cache(self, identifier: str) -> Optional[Dict]:
        """Get entity from database cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT entity_data, last_updated FROM channel_cache 
                WHERE identifier = ? AND last_updated > datetime('now', '-1 hour')
            ''', (identifier,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            return None
            
        except Exception as e:
            logger.error(f"Error reading from database cache: {e}")
            return None
    
    def _save_to_db_cache(self, identifier: str, info: Dict):
        """Save entity to database cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO channel_cache 
                (identifier, entity_data, subscribers, title, username)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                identifier,
                json.dumps(info),
                info.get('subscribers', 0),
                info.get('title', ''),
                info.get('username', '')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving to database cache: {e}")
    
    def _save_search_history(self, query: str, results: List[Dict]):
        """Save search query and results to history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO search_history (query, results)
                VALUES (?, ?)
            ''', (query, json.dumps(results)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving search history: {e}")
    
    def get_search_history(self, limit: int = 10) -> List[Dict]:
        """Get recent search history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT query, results, search_date FROM search_history 
                ORDER BY search_date DESC LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "query": row[0],
                    "results": json.loads(row[1]),
                    "date": row[2]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting search history: {e}")
            return []
    
    def clear_cache(self):
        """Clear all caches"""
        self.cache.clear()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM channel_cache")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error clearing database cache: {e}")
