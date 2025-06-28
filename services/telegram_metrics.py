import asyncio
import logging
from typing import Dict, List, Optional
from .enhanced_telegram_client import EnhancedTelegramClient
from .telegram_monitor import TelegramMonitorService

logger = logging.getLogger(__name__)

# Configuration
API_ID = 28511289
API_HASH = 'ff11a2ac8a96b6a91e0b843c51275628'

# Global instances
_enhanced_client = None
_monitor_service = None

def get_enhanced_client() -> EnhancedTelegramClient:
    """Get or create enhanced Telegram client"""
    global _enhanced_client
    if _enhanced_client is None:
        _enhanced_client = EnhancedTelegramClient('session_name', API_ID, API_HASH)
    return _enhanced_client

def get_monitor_service() -> TelegramMonitorService:
    """Get or create monitor service"""
    global _monitor_service
    if _monitor_service is None:
        _monitor_service = TelegramMonitorService(API_ID, API_HASH)
    return _monitor_service

async def get_channel_info_async(channel_username: str, force_refresh: bool = False) -> Optional[Dict]:
    """
    Get channel information asynchronously with caching
    
    Args:
        channel_username: Channel username or ID
        force_refresh: Force refresh from server
        
    Returns:
        Dictionary with channel information
    """
    client = get_enhanced_client()
    return await client.get_entity_info(channel_username, force_refresh)

def get_channel_info(channel_username: str, force_refresh: bool = False) -> Optional[Dict]:
    """
    Synchronous wrapper for get_channel_info_async
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(get_channel_info_async(channel_username, force_refresh))
                )
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(get_channel_info_async(channel_username, force_refresh))
    except Exception as e:
        logger.error(f"Error getting channel info for {channel_username}: {e}")
        return None

async def get_last_posts_async(channel_username: str, limit: int = 10) -> List[Dict]:
    """
    Get last posts asynchronously with enhanced information
    
    Args:
        channel_username: Channel username or ID
        limit: Number of posts to retrieve
        
    Returns:
        List of post dictionaries
    """
    client = get_enhanced_client()
    messages = await client.get_recent_messages(channel_username, limit)
    
    # Convert to legacy format for compatibility
    posts = []
    for msg in messages:
        posts.append({
            "text": msg.get("text", ""),
            "date": msg.get("date", ""),
            "views": msg.get("views", 0),
            "replies": msg.get("replies", 0),
            "reactions": msg.get("reactions_count", 0),
            "forwards": msg.get("forwards", 0),
            "media_type": msg.get("media_type")
        })
    
    return posts

def get_last_posts(channel_username: str, limit: int = 10) -> List[Dict]:
    """
    Synchronous wrapper for get_last_posts_async
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(get_last_posts_async(channel_username, limit))
                )
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(get_last_posts_async(channel_username, limit))
    except Exception as e:
        logger.error(f"Error getting last posts for {channel_username}: {e}")
        return []

async def batch_get_channels_info(channel_usernames: List[str]) -> Dict[str, Optional[Dict]]:
    """
    Get information for multiple channels in batch
    
    Args:
        channel_usernames: List of channel usernames or IDs
        
    Returns:
        Dictionary mapping username to channel info
    """
    client = get_enhanced_client()
    return await client.batch_get_entities(channel_usernames)

async def search_channels(query: str, limit: int = 50) -> List[Dict]:
    """
    Search for channels by name or description
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of matching channels
    """
    client = get_enhanced_client()
    return await client.search_channels(query, limit)

def start_monitoring(channels: List[str], callback=None, update_interval: int = 30):
    """
    Start monitoring channels for real-time updates
    
    Args:
        channels: List of channel usernames/IDs to monitor
        callback: Callback function for updates
        update_interval: Update interval in seconds
    """
    async def _start_monitoring():
        monitor = get_monitor_service()
        
        # Add channels to monitoring
        for channel in channels:
            await monitor.add_channel(channel, callback)
        
        # Start monitoring
        await monitor.start_monitoring(update_interval)
    
    # Run in background
    asyncio.create_task(_start_monitoring())

def stop_monitoring():
    """Stop monitoring all channels"""
    async def _stop_monitoring():
        monitor = get_monitor_service()
        await monitor.stop_monitoring()
    
    asyncio.create_task(_stop_monitoring())

def get_monitoring_stats() -> List[Dict]:
    """Get statistics for all monitored channels"""
    monitor = get_monitor_service()
    return monitor.get_all_stats()

def clear_cache():
    """Clear all caches"""
    client = get_enhanced_client()
    client.clear_cache()

def get_search_history(limit: int = 10) -> List[Dict]:
    """Get recent search history"""
    client = get_enhanced_client()
    return client.get_search_history(limit)