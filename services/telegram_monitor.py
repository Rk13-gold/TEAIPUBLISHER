"""
Real-time monitoring service for Telegram channels and groups
"""
import asyncio
import time
from typing import Dict, List, Callable, Optional
from datetime import datetime, timedelta
import logging
from .enhanced_telegram_client import EnhancedTelegramClient

logger = logging.getLogger(__name__)


class TelegramMonitorService:
    """Service for real-time monitoring of multiple Telegram channels/groups"""
    
    def __init__(self, api_id: int, api_hash: str, session_name: str = "monitor_session"):
        self.client = EnhancedTelegramClient(session_name, api_id, api_hash)
        self.monitored_channels: Dict[str, Dict] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.is_monitoring = False
        self.monitor_task = None
        self.update_interval = 30  # seconds
        
    async def add_channel(self, identifier: str, callback: Optional[Callable] = None) -> bool:
        """
        Add a channel/group to monitoring list
        
        Args:
            identifier: Channel username, ID, or URL
            callback: Optional callback function for updates
            
        Returns:
            True if successfully added
        """
        try:
            # Get channel info to validate
            info = await self.client.get_entity_info(identifier)
            if not info:
                logger.error(f"Could not find channel: {identifier}")
                return False
            
            self.monitored_channels[identifier] = {
                "info": info,
                "last_message_id": 0,
                "last_update": datetime.now(),
                "message_count": 0,
                "subscriber_count": info.get("subscribers", 0),
                "subscriber_history": []
            }
            
            # Add callback if provided
            if callback:
                if identifier not in self.callbacks:
                    self.callbacks[identifier] = []
                self.callbacks[identifier].append(callback)
            
            logger.info(f"Added channel to monitoring: {info.get('title', identifier)}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding channel {identifier}: {e}")
            return False
    
    def remove_channel(self, identifier: str):
        """Remove channel from monitoring"""
        self.monitored_channels.pop(identifier, None)
        self.callbacks.pop(identifier, None)
        logger.info(f"Removed channel from monitoring: {identifier}")
    
    def add_callback(self, identifier: str, callback: Callable):
        """Add callback for channel updates"""
        if identifier not in self.callbacks:
            self.callbacks[identifier] = []
        self.callbacks[identifier].append(callback)
    
    async def start_monitoring(self, update_interval: int = 30):
        """Start real-time monitoring of all added channels"""
        self.update_interval = update_interval
        self.is_monitoring = True
        
        logger.info(f"Starting monitoring of {len(self.monitored_channels)} channels")
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        return self.monitor_task
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        await self.client.disconnect()
        logger.info("Monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._check_all_channels()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _check_all_channels(self):
        """Check all monitored channels for updates"""
        if not self.monitored_channels:
            return
        
        # Check channels in batches to avoid overwhelming the API
        batch_size = 5
        identifiers = list(self.monitored_channels.keys())
        
        for i in range(0, len(identifiers), batch_size):
            batch = identifiers[i:i + batch_size]
            await asyncio.gather(*[self._check_channel(identifier) for identifier in batch])
            
            # Small delay between batches
            if i + batch_size < len(identifiers):
                await asyncio.sleep(1)
    
    async def _check_channel(self, identifier: str):
        """Check single channel for updates"""
        try:
            channel_data = self.monitored_channels[identifier]
            
            # Get recent messages
            messages = await self.client.get_recent_messages(identifier, limit=5)
            if not messages:
                return
            
            # Check for new messages
            latest_message_id = max(msg["id"] for msg in messages)
            if latest_message_id > channel_data["last_message_id"]:
                new_messages = [msg for msg in messages if msg["id"] > channel_data["last_message_id"]]
                
                # Update tracking data
                channel_data["last_message_id"] = latest_message_id
                channel_data["message_count"] += len(new_messages)
                channel_data["last_update"] = datetime.now()
                
                # Get updated channel info
                updated_info = await self.client.get_entity_info(identifier, force_refresh=True)
                if updated_info:
                    old_subscribers = channel_data["subscriber_count"]
                    new_subscribers = updated_info.get("subscribers", 0)
                    
                    if new_subscribers != old_subscribers:
                        channel_data["subscriber_count"] = new_subscribers
                        channel_data["subscriber_history"].append({
                            "count": new_subscribers,
                            "timestamp": datetime.now().isoformat(),
                            "change": new_subscribers - old_subscribers
                        })
                        
                        # Keep only last 100 history entries
                        if len(channel_data["subscriber_history"]) > 100:
                            channel_data["subscriber_history"] = channel_data["subscriber_history"][-100:]
                    
                    channel_data["info"] = updated_info
                
                # Trigger callbacks
                await self._trigger_callbacks(identifier, {
                    "type": "new_messages",
                    "messages": new_messages,
                    "channel_info": channel_data["info"],
                    "total_messages": channel_data["message_count"]
                })
            
        except Exception as e:
            logger.error(f"Error checking channel {identifier}: {e}")
    
    async def _trigger_callbacks(self, identifier: str, update_data: Dict):
        """Trigger all callbacks for a channel"""
        if identifier not in self.callbacks:
            return
        
        for callback in self.callbacks[identifier]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(identifier, update_data)
                else:
                    callback(identifier, update_data)
            except Exception as e:
                logger.error(f"Error in callback for {identifier}: {e}")
    
    def get_channel_stats(self, identifier: str) -> Optional[Dict]:
        """Get current statistics for a monitored channel"""
        if identifier not in self.monitored_channels:
            return None
        
        data = self.monitored_channels[identifier]
        return {
            "info": data["info"],
            "message_count": data["message_count"],
            "subscriber_count": data["subscriber_count"],
            "last_update": data["last_update"].isoformat(),
            "subscriber_growth": self._calculate_growth(data["subscriber_history"]),
            "activity_level": self._calculate_activity_level(data)
        }
    
    def get_all_stats(self) -> List[Dict]:
        """Get statistics for all monitored channels"""
        return [
            {"identifier": identifier, **self.get_channel_stats(identifier)}
            for identifier in self.monitored_channels.keys()
        ]
    
    def _calculate_growth(self, history: List[Dict]) -> Dict:
        """Calculate subscriber growth metrics"""
        if len(history) < 2:
            return {"daily": 0, "weekly": 0, "monthly": 0}
        
        now = datetime.now()
        daily_growth = 0
        weekly_growth = 0
        monthly_growth = 0
        
        # Calculate growth for different periods
        for entry in reversed(history):
            entry_time = datetime.fromisoformat(entry["timestamp"])
            age = (now - entry_time).days
            
            if age <= 1 and daily_growth == 0:
                daily_growth = entry["change"]
            elif age <= 7 and weekly_growth == 0:
                weekly_growth = entry["change"]
            elif age <= 30 and monthly_growth == 0:
                monthly_growth = entry["change"]
        
        return {
            "daily": daily_growth,
            "weekly": weekly_growth,
            "monthly": monthly_growth
        }
    
    def _calculate_activity_level(self, data: Dict) -> str:
        """Calculate activity level based on recent message frequency"""
        last_update = data["last_update"]
        hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
        
        if hours_since_update < 1:
            return "Very Active"
        elif hours_since_update < 6:
            return "Active"
        elif hours_since_update < 24:
            return "Moderate"
        else:
            return "Low Activity"
    
    async def bulk_add_channels(self, identifiers: List[str], callback: Optional[Callable] = None) -> Dict[str, bool]:
        """Add multiple channels to monitoring"""
        results = {}
        
        # Get entity info in batch
        entity_batch = await self.client.batch_get_entities(identifiers)
        
        for identifier in identifiers:
            if entity_batch.get(identifier):
                success = await self.add_channel(identifier, callback)
                results[identifier] = success
            else:
                results[identifier] = False
                logger.error(f"Could not add channel: {identifier}")
        
        return results
    
    async def search_and_monitor(self, query: str, limit: int = 10, callback: Optional[Callable] = None) -> List[str]:
        """Search for channels and add them to monitoring"""
        search_results = await self.client.search_channels(query, limit)
        
        added_channels = []
        for result in search_results:
            identifier = result.get("username") or str(result.get("id"))
            if identifier:
                success = await self.add_channel(identifier, callback)
                if success:
                    added_channels.append(identifier)
        
        return added_channels
