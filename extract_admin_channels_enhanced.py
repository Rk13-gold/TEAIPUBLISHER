#!/usr/bin/env python3
"""
Enhanced CLI tool for extracting admin channel IDs using the unified extractor
Supports both quick and comprehensive scans
"""
import sys
import os
import argparse
from typing import List, Dict

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.bot_channel_extractor import (
        BotChannelIDExtractor, 
        extract_admin_channel_ids_only,
        extract_admin_channel_ids
    )
except ImportError:
    from telegram_ai_publisher.utils.bot_channel_extractor import (
        BotChannelIDExtractor, 
        extract_admin_channel_ids_only,
        extract_admin_channel_ids
    )


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Extract Telegram channel IDs where your bot is administrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --token YOUR_BOT_TOKEN                    # Quick extraction (IDs only)
  %(prog)s --token YOUR_BOT_TOKEN --detailed         # Detailed extraction
  %(prog)s --token YOUR_BOT_TOKEN --comprehensive    # Comprehensive scan
  %(prog)s --token YOUR_BOT_TOKEN --save output.txt  # Save to file
  %(prog)s --token YOUR_BOT_TOKEN --members          # Include member channels
        """
    )
    
    parser.add_argument(
        '--token', '-t',
        required=True,
        help='Telegram Bot API token'
    )
    
    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed channel information (default: IDs only)'
    )
    
    parser.add_argument(
        '--comprehensive', '-c',
        action='store_true',
        help='Use comprehensive scan (slower but more thorough)'
    )
    
    parser.add_argument(
        '--members', '-m',
        action='store_true',
        help='Include channels where bot is member (not just admin)'
    )
    
    parser.add_argument(
        '--save', '-s',
        metavar='FILE',
        help='Save results to file'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (minimal output)'
    )
    
    parser.add_argument(
        '--search',
        metavar='CHANNEL_ID',
        help='Search for specific channel by ID or username'
    )
    
    args = parser.parse_args()
    
    # Header
    if not args.quiet:
        print("🤖 Telegram Admin Channel ID Extractor")
        print("=" * 50)
    
    try:
        extractor = BotChannelIDExtractor(args.token)
        
        # Test bot token
        if not args.quiet:
            print("🔍 Testing bot token...")
        
        bot_test = extractor.test_bot_token()
        if not bot_test['success']:
            print(f"❌ Bot token test failed: {bot_test['error']}")
            sys.exit(1)
        
        if not args.quiet:
            print(f"✅ {bot_test['message']}")
        
        # Handle search mode
        if args.search:
            handle_search_mode(extractor, args)
            return
        
        # Handle extraction mode
        if args.detailed:
            handle_detailed_extraction(extractor, args)
        else:
            handle_simple_extraction(extractor, args)
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


def handle_search_mode(extractor: BotChannelIDExtractor, args):
    """Handle search for specific channel"""
    if not args.quiet:
        print(f"🔍 Searching for channel: {args.search}")
    
    channel_info = extractor.get_channel_info_by_id(args.search)
    
    if not channel_info:
        print(f"❌ Channel not found: {args.search}")
        return
    
    # Check admin status
    admin_info = extractor.check_admin_permissions(channel_info['id'])
    is_admin = admin_info.get('is_admin', False)
    
    print(f"\n📊 Channel Information:")
    print(f"  ID: {channel_info['id']}")
    print(f"  Title: {channel_info['title']}")
    print(f"  Username: @{channel_info.get('username', 'N/A')}")
    print(f"  Type: {channel_info['type'].title()}")
    print(f"  Members: {channel_info.get('member_count', 'Unknown')}")
    print(f"  Private: {'Yes' if channel_info.get('is_private', False) else 'No'}")
    print(f"  Bot Status: {'🔧 Admin' if is_admin else '👥 Member/No Access'}")
    
    if is_admin:
        print(f"  Admin Role: {admin_info.get('status', 'Unknown').title()}")


def handle_simple_extraction(extractor: BotChannelIDExtractor, args):
    """Handle simple ID-only extraction"""
    if not args.quiet:
        scan_type = "comprehensive" if args.comprehensive else "quick"
        print(f"📡 Starting {scan_type} extraction (IDs only)...")
    
    if args.comprehensive:
        # Use comprehensive method
        channels = extractor.get_comprehensive_admin_channels(
            include_member_channels=args.members
        )
        # Filter for admin only if not including members
        if not args.members:
            admin_channel_ids = [ch['id'] for ch in channels if ch.get('is_admin', False)]
        else:
            admin_channel_ids = [ch['id'] for ch in channels]
    else:
        # Use quick method
        admin_channel_ids = extractor.get_admin_channel_ids_only()
    
    # Display results
    if not args.quiet:
        print(f"\n🎯 Found {len(admin_channel_ids)} channels:")
        print("=" * 30)
    
    for i, channel_id in enumerate(admin_channel_ids, 1):
        if args.quiet:
            print(channel_id)
        else:
            print(f"{i:2d}. {channel_id}")
    
    # Save to file if requested
    if args.save:
        save_ids_to_file(admin_channel_ids, args.save, args.quiet)


def handle_detailed_extraction(extractor: BotChannelIDExtractor, args):
    """Handle detailed extraction with full channel info"""
    if not args.quiet:
        scan_type = "comprehensive" if args.comprehensive else "quick"
        print(f"📡 Starting {scan_type} extraction (detailed)...")
    
    if args.comprehensive:
        admin_channels = extractor.get_comprehensive_admin_channels(
            include_member_channels=args.members
        )
    else:
        admin_channels = extractor.get_admin_channels_detailed(check_from_updates=True)
        if args.members:
            # For quick scan, we need to manually include member channels
            pass  # The existing method only returns admin channels
    
    # Display results
    if not args.quiet:
        print(f"\n🎯 Found {len(admin_channels)} channels:")
        print("=" * 80)
    
    for i, channel in enumerate(admin_channels, 1):
        is_admin = channel.get('is_admin', True)  # Default True for backward compatibility
        status_emoji = "🔧" if is_admin else "👥"
        username_str = f"@{channel['username']}" if channel.get('username') else "Private"
        
        if args.quiet:
            print(f"{channel['id']}\t{channel['title']}\t{username_str}\t{channel['type']}")
        else:
            print(f"{i:2d}. {channel['title']}")
            print(f"    ID: {channel['id']}")
            print(f"    Username: {username_str}")
            print(f"    Type: {channel['type'].title()}")
            print(f"    Status: {status_emoji} {channel.get('admin_status', 'Unknown').title()}")
            print()
    
    # Save to file if requested
    if args.save:
        save_detailed_to_file(admin_channels, args.save, args.quiet)


def save_ids_to_file(channel_ids: List[int], filename: str, quiet: bool = False):
    """Save channel IDs to file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Admin Channel IDs extracted by Telegram AI Publisher\n")
            f.write(f"# Total channels: {len(channel_ids)}\n\n")
            
            for channel_id in channel_ids:
                f.write(f"{channel_id}\n")
        
        if not quiet:
            print(f"💾 Saved {len(channel_ids)} channel IDs to {filename}")
            
    except Exception as e:
        print(f"❌ Error saving to file: {str(e)}")


def save_detailed_to_file(channels: List[Dict], filename: str, quiet: bool = False):
    """Save detailed channel info to file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Detailed Admin Channel Information\n")
            f.write(f"# Total channels: {len(channels)}\n\n")
            
            for channel in channels:
                is_admin = channel.get('is_admin', True)
                status_emoji = "🔧" if is_admin else "👥"
                username_str = f"@{channel['username']}" if channel.get('username') else "Private"
                
                f.write(f"Channel: {channel['title']}\n")
                f.write(f"ID: {channel['id']}\n")
                f.write(f"Username: {username_str}\n")
                f.write(f"Type: {channel['type'].title()}\n")
                f.write(f"Status: {status_emoji} {channel.get('admin_status', 'Unknown').title()}\n")
                f.write("-" * 40 + "\n\n")
        
        if not quiet:
            print(f"💾 Saved detailed info for {len(channels)} channels to {filename}")
            
    except Exception as e:
        print(f"❌ Error saving to file: {str(e)}")


if __name__ == "__main__":
    main()
