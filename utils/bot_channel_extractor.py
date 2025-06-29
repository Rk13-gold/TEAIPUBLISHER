"""
Bot Channel ID Extractor - Simple modular function to extract channel IDs using bot token
"""
import requests
import json
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class BotChannelIDExtractor:
    """Simple extractor for channel IDs using Telegram Bot API"""
    
    def __init__(self, bot_token: str):
        """
        Initialize with bot token
        Args:
            bot_token: Telegram Bot API token
        """
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = requests.Session()
        self.session.timeout = 30
    
    def _make_request(self, method: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to Telegram Bot API"""
        try:
            url = f"{self.base_url}/{method}"
            response = self.session.get(url, params=params or {})
            response.raise_for_status()
            
            data = response.json()
            if data.get('ok'):
                return data.get('result')
            else:
                error_desc = data.get('description', 'Unknown error')
                logger.error(f"Bot API error for {method}: {error_desc}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {method}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {method}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {method}: {e}")
            return None
    
    def test_bot_token(self) -> Dict[str, any]:
        """
        Test if the bot token is valid and return bot info
        Returns:
            Dict with bot info or error info
        """
        try:
            result = self._make_request('getMe')
            if result:
                return {
                    'success': True,
                    'bot_id': result.get('id'),
                    'bot_name': result.get('first_name', 'Unknown'),
                    'bot_username': result.get('username', 'unknown'),
                    'message': f"Bot connected: @{result.get('username', 'unknown')} ({result.get('first_name', 'Unknown')})"
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to get bot info - Invalid token or API error'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception testing bot: {str(e)}'
            }
    
    def get_channel_ids_from_updates(self, limit: int = 100) -> List[Dict]:
        """
        Get channel IDs from recent updates (messages sent to bot)
        This method gets channels where the bot received messages
        
        Args:
            limit: Maximum number of updates to check
            
        Returns:
            List of channel info dictionaries
        """
        channels = []
        try:
            # Get updates
            result = self._make_request('getUpdates', {'limit': limit})
            if not result:
                return channels
            
            seen_chats = set()
            
            for update in result:
                chat = None
                
                # Check different types of updates
                if 'message' in update:
                    chat = update['message'].get('chat')
                elif 'channel_post' in update:
                    chat = update['channel_post'].get('chat')
                elif 'edited_channel_post' in update:
                    chat = update['edited_channel_post'].get('chat')
                
                if chat and chat['id'] not in seen_chats:
                    chat_type = chat.get('type', 'unknown')
                    
                    # Only include channels and groups
                    if chat_type in ['channel', 'supergroup', 'group']:
                        seen_chats.add(chat['id'])
                        
                        channels.append({
                            'id': chat['id'],
                            'title': chat.get('title', 'Unknown'),
                            'username': chat.get('username'),
                            'type': chat_type,
                            'is_private': chat.get('username') is None
                        })
            
            return channels
            
        except Exception as e:
            logger.error(f"Error getting channels from updates: {e}")
            return []
    
    def check_admin_permissions(self, chat_id: int) -> Dict[str, any]:
        """
        Check if bot is admin in a specific chat
        
        Args:
            chat_id: Chat ID to check
            
        Returns:
            Dict with admin status and permissions
        """
        try:
            # First get bot info to get bot user ID
            bot_info = self._make_request('getMe')
            if not bot_info:
                return {'is_admin': False, 'error': 'Cannot get bot info'}
            
            bot_user_id = bot_info['id']
            
            # Get chat member info for the bot
            result = self._make_request('getChatMember', {
                'chat_id': chat_id,
                'user_id': bot_user_id
            })
            
            if not result:
                return {'is_admin': False, 'error': 'Cannot get chat member info'}
            
            status = result.get('status', 'member')
            is_admin = status in ['administrator', 'creator']
            
            permissions = {}
            if is_admin and status == 'administrator':
                # Extract admin permissions
                permissions = {
                    'can_be_edited': result.get('can_be_edited', False),
                    'can_manage_chat': result.get('can_manage_chat', False),
                    'can_change_info': result.get('can_change_info', False),
                    'can_post_messages': result.get('can_post_messages', False),
                    'can_edit_messages': result.get('can_edit_messages', False),
                    'can_delete_messages': result.get('can_delete_messages', False),
                    'can_invite_users': result.get('can_invite_users', False),
                    'can_restrict_members': result.get('can_restrict_members', False),
                    'can_pin_messages': result.get('can_pin_messages', False),
                    'can_promote_members': result.get('can_promote_members', False),
                }
            
            return {
                'is_admin': is_admin,
                'status': status,
                'permissions': permissions
            }
            
        except Exception as e:
            return {'is_admin': False, 'error': f'Exception: {str(e)}'}
    
    def get_admin_channel_ids_only(self) -> List[int]:
        """
        Get only the IDs of channels and groups where bot is admin
        
        Returns:
            List of channel/group IDs where bot is administrator
        """
        admin_channel_ids = []
        
        try:
            # Get channels from updates first
            channels = self.get_channel_ids_from_updates()
            
            print(f"🔍 Found {len(channels)} channels from updates, checking admin status...")
            
            for i, channel in enumerate(channels):
                print(f"Checking {i+1}/{len(channels)}: {channel['title']} ({channel['id']})")
                
                # Check if bot is admin
                admin_info = self.check_admin_permissions(channel['id'])
                
                if admin_info.get('is_admin', False):
                    admin_channel_ids.append(channel['id'])
                    print(f"  ✅ Admin in: {channel['title']} -> ID: {channel['id']}")
                else:
                    print(f"  ❌ Not admin in: {channel['title']}")
            
            return admin_channel_ids
            
        except Exception as e:
            logger.error(f"Error getting admin channel IDs: {e}")
            return []
    
    def get_admin_channels_detailed(self, check_from_updates: bool = True) -> List[Dict]:
        """
        Get detailed info of all channels and groups where bot is admin
        
        Args:
            check_from_updates: Whether to check channels from recent updates
            
        Returns:
            List of detailed admin channel info
        """
        admin_channels = []
        
        try:
            if check_from_updates:
                # Get channels from updates first
                channels = self.get_channel_ids_from_updates()
                
                print(f"Found {len(channels)} channels from updates, checking admin status...")
                
                for i, channel in enumerate(channels):
                    print(f"Checking {i+1}/{len(channels)}: {channel['title']} ({channel['id']})")
                    
                    # Check if bot is admin
                    admin_info = self.check_admin_permissions(channel['id'])
                    
                    if admin_info.get('is_admin', False):
                        channel_info = {
                            'id': channel['id'],
                            'title': channel['title'],
                            'username': channel.get('username'),
                            'type': channel['type'],
                            'is_private': channel['is_private'],
                            'admin_status': admin_info.get('status'),
                            'permissions': admin_info.get('permissions', {})
                        }
                        admin_channels.append(channel_info)
                        print(f"  ✅ Admin in: {channel['title']}")
                    else:
                        print(f"  ❌ Not admin in: {channel['title']}")
            
            return admin_channels
            
        except Exception as e:
            logger.error(f"Error getting admin channels: {e}")
            return []
    
    def get_channel_info_by_id(self, channel_id: str) -> Optional[Dict]:
        """
        Get detailed channel information by ID
        
        Args:
            channel_id: Channel ID (can be @username or numeric ID)
            
        Returns:
            Dict with channel info or None if not found
        """
        try:
            result = self._make_request('getChat', {'chat_id': channel_id})
            if not result:
                return None
            
            # Get member count
            member_count = None
            try:
                count_result = self._make_request('getChatMemberCount', {'chat_id': channel_id})
                if count_result is not None:
                    member_count = count_result
            except:
                pass
            
            return {
                'id': result.get('id'),
                'title': result.get('title', 'Unknown'),
                'username': result.get('username'),
                'type': result.get('type', 'unknown'),
                'description': result.get('description'),
                'member_count': member_count,
                'is_private': result.get('username') is None,
                'invite_link': result.get('invite_link')
            }
            
        except Exception as e:
            logger.error(f"Error getting channel info for {channel_id}: {e}")
            return None


def extract_admin_channel_ids_only(bot_token: str, verbose: bool = True) -> Tuple[bool, List[int], str]:
    """
    Extract ONLY the IDs of channels where bot is admin
    
    Args:
        bot_token: Telegram Bot API token
        verbose: Whether to print progress messages
        
    Returns:
        Tuple of (success, list_of_channel_ids, message)
    """
    try:
        if verbose:
            print("🤖 Extracting Admin Channel IDs...")
        
        extractor = BotChannelIDExtractor(bot_token)
        
        # Test bot token first
        if verbose:
            print("🔍 Testing bot token...")
        
        bot_test = extractor.test_bot_token()
        if not bot_test['success']:
            return False, [], f"Bot token test failed: {bot_test['error']}"
        
        if verbose:
            print(f"✅ {bot_test['message']}")
            print("📡 Searching for admin channels...")
        
        # Get admin channel IDs only
        admin_channel_ids = extractor.get_admin_channel_ids_only()
        
        if verbose:
            print(f"\n🎯 Found {len(admin_channel_ids)} admin channels/groups:")
            print("=" * 50)
            
            for i, channel_id in enumerate(admin_channel_ids, 1):
                print(f"{i:2d}. ID: {channel_id}")
            
            print("=" * 50)
            print("📋 Channel IDs (ready to copy):")
            for channel_id in admin_channel_ids:
                print(channel_id)
        
        success_message = f"Successfully found {len(admin_channel_ids)} admin channel IDs"
        return True, admin_channel_ids, success_message
        
    except Exception as e:
        error_message = f"Error extracting channel IDs: {str(e)}"
        if verbose:
            print(f"❌ {error_message}")
        return False, [], error_message


def extract_admin_channel_ids(bot_token: str, verbose: bool = True) -> Tuple[bool, List[Dict], str]:
    """
    Extract detailed info of admin channels (original function)
    
    Args:
        bot_token: Telegram Bot API token
        verbose: Whether to print progress messages
        
    Returns:
        Tuple of (success, list_of_channels, message)
    """
    try:
        if verbose:
            print("🤖 Initializing Bot Channel ID Extractor...")
        
        extractor = BotChannelIDExtractor(bot_token)
        
        # Test bot token first
        if verbose:
            print("🔍 Testing bot token...")
        
        bot_test = extractor.test_bot_token()
        if not bot_test['success']:
            return False, [], f"Bot token test failed: {bot_test['error']}"
        
        if verbose:
            print(f"✅ {bot_test['message']}")
            print("📡 Searching for admin channels...")
        
        # Get admin channels with details
        admin_channels = extractor.get_admin_channels_detailed(check_from_updates=True)
        
        if verbose:
            print(f"\n🎯 Found {len(admin_channels)} admin channels/groups:")
            print("=" * 60)
            
            for i, channel in enumerate(admin_channels, 1):
                username_str = f"@{channel['username']}" if channel['username'] else "Private"
                print(f"{i:2d}. {channel['title']}")
                print(f"    ID: {channel['id']}")
                print(f"    Username: {username_str}")
                print(f"    Type: {channel['type'].title()}")
                print(f"    Status: {channel['admin_status'].title()}")
                print()
        
        success_message = f"Successfully found {len(admin_channels)} admin channels/groups"
        return True, admin_channels, success_message
        
    except Exception as e:
        error_message = f"Error extracting channel IDs: {str(e)}"
        if verbose:
            print(f"❌ {error_message}")
        return False, [], error_message


# Convenience function for quick testing
def quick_extract_ids(bot_token: str) -> None:
    """
    Quick function to extract and print channel IDs
    
    Args:
        bot_token: Telegram Bot API token
    """
    print("🚀 Quick Channel ID Extraction")
    print("=" * 40)
    
    success, channels, message = extract_admin_channel_ids(bot_token, verbose=True)
    
    if success and channels:
        print("\n📋 Summary - Channel IDs:")
        print("-" * 30)
        for channel in channels:
            print(f"{channel['id']:15} | {channel['title']}")
        
        print(f"\n💾 Total: {len(channels)} admin channels found")
    else:
        print(f"\n❌ {message}")


def quick_extract_ids_only(bot_token: str) -> List[int]:
    """
    Quick function to extract ONLY the IDs (no verbose output)
    
    Args:
        bot_token: Telegram Bot API token
        
    Returns:
        List of channel IDs where bot is admin
    """
    print("🔍 Extracting admin channel IDs...")
    
    success, channel_ids, message = extract_admin_channel_ids_only(bot_token, verbose=False)
    
    if success:
        print(f"✅ Found {len(channel_ids)} admin channels")
        print("📋 Channel IDs:")
        for channel_id in channel_ids:
            print(f"  {channel_id}")
        return channel_ids
    else:
        print(f"❌ {message}")
        return []


if __name__ == "__main__":
    # Example usage
    test_token = "YOUR_BOT_TOKEN_HERE"
    
    print("Bot Channel ID Extractor - Test Mode")
    print("Please set your bot token in the test_token variable")
    
    if test_token != "YOUR_BOT_TOKEN_HERE":
        quick_extract_ids(test_token)
    else:
        print("Please set a valid bot token to test this module.")
