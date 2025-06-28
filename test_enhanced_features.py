"""
Simple test script to verify the enhanced features work
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all imports work correctly"""
    print("Testing imports...")
    
    try:
        from services.enhanced_telegram_client import EnhancedTelegramClient, TelegramEntityCache
        print("✅ Enhanced Telegram Client imported successfully")
    except ImportError as e:
        print(f"❌ Error importing enhanced client: {e}")
        return False
    
    try:
        from services.telegram_monitor import TelegramMonitorService
        print("✅ Telegram Monitor Service imported successfully")
    except ImportError as e:
        print(f"❌ Error importing monitor service: {e}")
        return False
    
    try:
        from services.telegram_metrics import get_enhanced_client, get_monitor_service
        print("✅ Enhanced metrics functions imported successfully")
    except ImportError as e:
        print(f"❌ Error importing enhanced metrics: {e}")
        return False
    
    try:
        from utils.channel_config import ChannelConfigManager, ChannelConfig
        print("✅ Channel config manager imported successfully")
    except ImportError as e:
        print(f"❌ Error importing channel config: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality without requiring Telegram connection"""
    print("\nTesting basic functionality...")
    
    try:
        # Test cache system
        from services.enhanced_telegram_client import TelegramEntityCache
        cache = TelegramEntityCache(cache_duration=3600)
        
        # Test cache operations
        cache.set("test_key", {"title": "Test Channel", "id": 123})
        cached_data = cache.get("test_key")
        
        if cached_data and cached_data.get("title") == "Test Channel":
            print("✅ Cache system working correctly")
        else:
            print("❌ Cache system not working")
            return False
        
        # Test channel config manager
        from utils.channel_config import ChannelConfigManager
        config_manager = ChannelConfigManager("test_config.json", "test_channels.db")
        
        # Test adding a channel
        success = config_manager.add_channel(
            username="test_channel",
            title="Test Channel",
            monitor_enabled=True
        )
        
        if success:
            print("✅ Channel config manager working correctly")
        else:
            print("❌ Channel config manager not working")
            return False
        
        # Test getting channel
        channel = config_manager.get_channel("test_channel")
        if channel and channel.username == "test_channel":
            print("✅ Channel retrieval working correctly")
        else:
            print("❌ Channel retrieval not working")
            return False
        
        # Cleanup test files
        import os
        try:
            os.remove("test_config.json")
            os.remove("test_channels.db")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error in basic functionality test: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Enhanced Telegram Features - Basic Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please check your installation.")
        return
    
    # Test basic functionality
    if not test_basic_functionality():
        print("\n❌ Basic functionality tests failed.")
        return
    
    print("\n✅ All basic tests passed!")
    print("\nNext steps:")
    print("1. Make sure you have valid Telegram API credentials")
    print("2. Update API_ID and API_HASH in services/telegram_metrics.py")
    print("3. Run: python main.py")
    print("4. Check the new 'Channel Manager' tab")
    
    print("\nFeatures ready to use:")
    print("• 🚀 Enhanced channel information retrieval with caching")
    print("• 📊 Real-time monitoring capabilities")
    print("• 🔍 Advanced channel search functionality")
    print("• 📈 Batch operations for multiple channels")
    print("• ⚙️ Persistent configuration management")

if __name__ == "__main__":
    main()
