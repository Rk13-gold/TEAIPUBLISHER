#!/usr/bin/env python3
"""
Test script for the unified admin channels tab
"""
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from gui.unified_admin_channels_tab import UnifiedAdminChannelsTab

def test_unified_tab():
    """Test the unified admin channels tab"""
    print("🧪 Testing Unified Admin Channels Tab...")
    
    app = QApplication(sys.argv)
    
    try:
        # Create the tab
        tab = UnifiedAdminChannelsTab()
        tab.setWindowTitle("🔧 Admin Channels Manager - Test")
        tab.resize(1000, 700)
        tab.show()
        
        print("✅ Tab created successfully!")
        print("✅ Window displayed!")
        print("📝 You can now test the interface manually.")
        print("🔹 Enter a bot token and try extracting channels.")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Error creating tab: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unified_tab()
