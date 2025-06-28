"""
Example script demonstrating the enhanced Telegram channel management features
"""
import asyncio
import time
from services.enhanced_telegram_client import EnhancedTelegramClient
from services.telegram_monitor import TelegramMonitorService
from utils.channel_config import ChannelConfigManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_ID = 28511289
API_HASH = 'ff11a2ac8a96b6a91e0b843c51275628'

async def demonstrate_enhanced_features():
    """Demonstrate the enhanced Telegram channel management features"""
    
    print("🚀 Demonstrating Enhanced Telegram Channel Management")
    print("=" * 60)
    
    # 1. Initialize enhanced client
    print("\n1. Initializing Enhanced Telegram Client...")
    client = EnhancedTelegramClient("demo_session", API_ID, API_HASH)
    
    # 2. Search for channels
    print("\n2. Searching for channels...")
    search_results = await client.search_channels("python", limit=10)
    print(f"Found {len(search_results)} Python-related channels")
    
    for i, channel in enumerate(search_results[:3], 1):
        print(f"   {i}. {channel.get('title', 'Unknown')} (@{channel.get('username', 'N/A')})")
        print(f"      Subscribers: {channel.get('subscribers', 'N/A')}")
        print(f"      ID: {channel.get('id', 'N/A')}")
    
    # 3. Get single channel info with caching
    print("\n3. Getting channel information with caching...")
    test_channel = "python"
    
    # First call (from server)
    start_time = time.time()
    channel_info = await client.get_entity_info(test_channel)
    first_call_time = time.time() - start_time
    
    if channel_info:
        print(f"   Channel: {channel_info.get('title', 'Unknown')}")
        print(f"   Subscribers: {channel_info.get('subscribers', 'N/A')}")
        print(f"   Time (first call): {first_call_time:.2f}s")
        
        # Second call (from cache)
        start_time = time.time()
        cached_info = await client.get_entity_info(test_channel)
        cached_call_time = time.time() - start_time
        print(f"   Time (cached call): {cached_call_time:.2f}s")
        print(f"   Speed improvement: {first_call_time/cached_call_time:.1f}x faster")
    
    # 4. Batch operations
    print("\n4. Demonstrating batch operations...")
    test_channels = ["python", "telegram", "programming"]
    
    start_time = time.time()
    batch_results = await client.batch_get_entities(test_channels, max_concurrent=3)
    batch_time = time.time() - start_time
    
    print(f"   Retrieved info for {len(batch_results)} channels in {batch_time:.2f}s")
    for channel, info in batch_results.items():
        if info:
            print(f"   - {info.get('title', 'Unknown')} (@{channel}): {info.get('subscribers', 'N/A')} subscribers")
    
    # 5. Get recent messages with enhanced info
    print("\n5. Getting recent messages with enhanced information...")
    messages = await client.get_recent_messages(test_channel, limit=5)
    
    for i, msg in enumerate(messages[:3], 1):
        print(f"   Message {i}:")
        print(f"      Text: {(msg.get('text', '')[:50] + '...') if len(msg.get('text', '')) > 50 else msg.get('text', 'No text')}")
        print(f"      Views: {msg.get('views', 0)}")
        print(f"      Reactions: {msg.get('reactions_count', 0)}")
        print(f"      Media: {msg.get('media_type', 'None')}")
    
    await client.disconnect()
    
    # 6. Demonstrate monitoring service
    print("\n6. Demonstrating Real-time Monitoring...")
    monitor = TelegramMonitorService(API_ID, API_HASH, "monitor_demo")
    
    # Callback function for updates
    def on_update(channel_id, update_data):
        print(f"   📢 Update from {channel_id}: {update_data.get('type', 'unknown')}")
        if update_data.get('type') == 'new_messages':
            print(f"      New messages: {len(update_data.get('messages', []))}")
    
    # Add channels to monitoring
    print("   Adding channels to monitoring...")
    for channel in test_channels[:2]:  # Monitor first 2 channels
        success = await monitor.add_channel(channel, on_update)
        if success:
            print(f"   ✅ Added {channel} to monitoring")
        else:
            print(f"   ❌ Failed to add {channel}")
    
    # Start monitoring for a short time
    print("   Starting monitoring (10 seconds demo)...")
    monitor_task = await monitor.start_monitoring(update_interval=5)
    
    # Let it run for 10 seconds
    await asyncio.sleep(10)
    
    # Get statistics
    stats = monitor.get_all_stats()
    print(f"   Monitoring statistics for {len(stats)} channels:")
    for stat in stats:
        info = stat.get('info', {})
        print(f"   - {info.get('title', 'Unknown')}: {stat.get('activity_level', 'Unknown')} activity")
    
    # Stop monitoring
    await monitor.stop_monitoring()
    print("   Monitoring stopped")
    
    # 7. Demonstrate configuration manager
    print("\n7. Demonstrating Channel Configuration Manager...")
    config_manager = ChannelConfigManager()
    
    # Add some channels
    for channel in test_channels:
        config_manager.add_channel(
            username=channel,
            title=f"Demo {channel.title()}",
            tags=["demo", "python" if "python" in channel else "general"],
            monitor_enabled=True,
            update_interval=30
        )
    
    # Show summary
    summary = config_manager.get_summary_stats()
    print(f"   Total channels configured: {summary['total_channels']}")
    print(f"   Monitored channels: {summary['monitored_channels']}")
    print(f"   Available tags: {', '.join(summary['all_tags'])}")
    
    # Add some demo statistics
    config_manager.record_stats("python", 150000, 10, 3.5, "Very Active")
    config_manager.add_alert("python", "high_activity", "Channel showing high activity", "info")
    
    # Show alerts
    alerts = config_manager.get_alerts()
    print(f"   Active alerts: {len(alerts)}")
    for alert in alerts[:2]:
        print(f"   - {alert['alert_type']}: {alert['message']}")
    
    # Export configuration
    export_success = config_manager.export_configurations("demo_export.json")
    print(f"   Configuration export: {'✅ Success' if export_success else '❌ Failed'}")
    
    print("\n🎉 Demonstration completed!")
    print("\nKey improvements implemented:")
    print("✅ Caching system for faster repeated queries")
    print("✅ Batch operations for multiple channels")
    print("✅ Real-time monitoring with callbacks")
    print("✅ Enhanced message information (media type, reactions, etc.)")
    print("✅ Persistent configuration management")
    print("✅ Statistics tracking and alerting")
    print("✅ Search history and export/import features")

def demonstrate_sync_features():
    """Demonstrate synchronous wrapper functions"""
    print("\n8. Demonstrating Synchronous Wrapper Functions...")
    
    from services.telegram_metrics import get_channel_info, get_last_posts, clear_cache
    
    # These functions automatically handle async execution
    print("   Getting channel info (sync)...")
    info = get_channel_info("python")
    if info:
        print(f"   Channel: {info.get('title', 'Unknown')}")
        print(f"   Subscribers: {info.get('subscribers', 'N/A')}")
    
    print("   Getting last posts (sync)...")
    posts = get_last_posts("python", limit=3)
    print(f"   Retrieved {len(posts)} posts")
    
    print("   Clearing cache...")
    clear_cache()
    print("   Cache cleared ✅")

if __name__ == "__main__":
    print("Starting Enhanced Telegram Channel Management Demo...")
    
    # Run async demonstration
    asyncio.run(demonstrate_enhanced_features())
    
    # Run sync demonstration
    demonstrate_sync_features()
    
    print("\n" + "=" * 60)
    print("Demo completed! Check the new GUI tab 'Channel Manager' for the full interface.")
