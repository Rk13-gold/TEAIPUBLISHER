#!/usr/bin/env python3
"""
Final Verification Script - Telegram AI Publisher Admin Channels System
Tests all components to ensure everything is working correctly.
"""
import sys
import os
from pathlib import Path

def test_file_structure():
    """Verify all required files exist"""
    print("🔍 Checking file structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "gui/main_window.py",
        "gui/admin_channels_tab.py",
        "services/enhanced_telegram_client.py",
        "services/telegram_metrics.py",
        "core/config.py",
        "core/database.py",
        "core/logger.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print("  🎉 All required files present!")
    return True

def test_imports():
    """Test critical imports"""
    print("\n📦 Testing imports...")
    
    try:
        # Core imports
        from core.config import Config
        print("  ✅ Core config import OK")
        
        from core.database import Database
        print("  ✅ Database import OK")
        
        # GUI imports
        from gui.admin_channels_tab import AdminChannelsTab
        print("  ✅ Admin channels tab import OK")
        
        from gui.main_window import MainWindow
        print("  ✅ Main window import OK")
        
        # Services imports
        from services.enhanced_telegram_client import EnhancedTelegramClient
        print("  ✅ Enhanced Telegram client import OK")
        
        print("  🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_dependencies():
    """Check if all required packages are installed"""
    print("\n🔧 Checking dependencies...")
    
    required_packages = [
        "PySide6",
        "requests", 
        "sqlalchemy",
        "telethon",
        "qasync"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n  📋 Install missing packages with:")
        print(f"     pip install {' '.join(missing_packages)}")
        return False
    
    print("  🎉 All dependencies installed!")
    return True

def test_gui_creation():
    """Test if GUI components can be created"""
    print("\n🎨 Testing GUI creation...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from gui.admin_channels_tab import AdminChannelsTab
        from core.config import Config
        
        # Create minimal app
        app = QApplication([])
        
        # Test config creation
        config = Config()
        print("  ✅ Config created successfully")
        
        # Test tab creation
        tab = AdminChannelsTab(config)
        print("  ✅ Admin channels tab created successfully")
        
        print("  🎉 GUI components working!")
        return True
        
    except Exception as e:
        print(f"  ❌ GUI creation error: {e}")
        return False

def run_verification():
    """Run all verification tests"""
    print("🚀 TELEGRAM AI PUBLISHER - ADMIN CHANNELS SYSTEM VERIFICATION\n")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies), 
        ("Python Imports", test_imports),
        ("GUI Creation", test_gui_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("✅ The Admin Channels system is ready for use.")
        print("\n💡 Next steps:")
        print("   1. Configure Telegram API credentials in core/config.py")
        print("   2. Run: python main.py")
        print("   3. Navigate to '🤖 Admin Channels' tab")
        print("   4. Click 'Refresh Channels' to load your admin channels")
        return True
    else:
        print(f"\n⚠️  {total - passed} issues found. Please resolve them first.")
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
