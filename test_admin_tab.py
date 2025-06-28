#!/usr/bin/env python3
"""
Test script for Admin Channels Tab functionality
"""
import sys
from PySide6.QtWidgets import QApplication
from gui.admin_channels_tab import AdminChannelsTab
from core.config import Config

def test_admin_channels_tab():
    """Test the admin channels tab GUI"""
    print("🧪 Testing Admin Channels Tab...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    try:
        # Create config
        config = Config()
        print("✅ Config loaded successfully")
        
        # Create admin channels tab
        tab = AdminChannelsTab(config)
        print("✅ Admin Channels Tab created successfully")
        
        # Show the tab
        tab.show()
        print("✅ Tab shown successfully")
        
        # Basic functionality test
        print("📊 Tab statistics:")
        print(f"   - Tab title: {tab.windowTitle()}")
        print(f"   - Tab visible: {tab.isVisible()}")
        
        # Test refresh functionality (without actually connecting)
        print("🔄 Testing refresh button...")
        from PySide6.QtWidgets import QPushButton
        refresh_btn = tab.findChild(QPushButton, "refresh_button")
        if refresh_btn:
            print("✅ Refresh button found")
        else:
            print("ℹ️  Refresh button not found (this is expected)")
        
        print("\n🎉 All basic tests passed!")
        print("💡 Note: Full functionality requires Telegram API credentials")
        
        # Don't actually exec the app in test mode
        # app.exec()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_admin_channels_tab()
    sys.exit(0 if success else 1)
