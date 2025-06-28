#!/usr/bin/env python3
"""
Bot Channel ID Extractor - Standalone Tool
Simple script to extract channel IDs using bot token
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.bot_channel_extractor import quick_extract_ids, extract_admin_channel_ids


def main():
    """Main function"""
    print("🤖 Telegram Bot Channel ID Extractor")
    print("=" * 50)
    print()
    
    # Check if token is provided as argument
    if len(sys.argv) > 1:
        bot_token = sys.argv[1]
        print(f"Using token from command line argument")
    else:
        # Ask for token interactively
        print("Please enter your Telegram Bot Token:")
        print("(Format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)")
        print()
        bot_token = input("Bot Token: ").strip()
    
    if not bot_token:
        print("❌ No bot token provided. Exiting.")
        return 1
    
    print(f"\n🔍 Processing with token: {bot_token[:10]}...{bot_token[-10:]}")
    print()
    
    try:
        # Extract channel IDs
        success, channels, message = extract_admin_channel_ids(bot_token, verbose=True)
        
        if success and channels:
            print("\n" + "="*60)
            print("📋 CHANNEL IDs - COPY THESE:")
            print("="*60)
            
            for channel in channels:
                print(channel['id'])
            
            print("="*60)
            print(f"Total: {len(channels)} admin channels found")
            
            # Option to save to file
            print("\nDo you want to save these IDs to a file? (y/n): ", end="")
            if input().lower().startswith('y'):
                filename = f"channel_ids_{len(channels)}.txt"
                with open(filename, 'w') as f:
                    for channel in channels:
                        f.write(f"{channel['id']}\n")
                print(f"💾 IDs saved to: {filename}")
            
            return 0
        else:
            print(f"\n❌ {message}")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1


def run_gui():
    """Run the GUI version"""
    try:
        from utils.channel_id_extractor_gui import run_channel_extractor
        return run_channel_extractor()
    except ImportError as e:
        print(f"❌ GUI not available: {e}")
        print("Make sure PySide6 is installed: pip install PySide6")
        return 1


if __name__ == "__main__":
    print("Choose extraction mode:")
    print("1. Command Line (CLI)")
    print("2. Graphical Interface (GUI)")
    print()
    
    choice = input("Enter choice (1 or 2, default=1): ").strip()
    
    if choice == "2":
        sys.exit(run_gui())
    else:
        sys.exit(main())
