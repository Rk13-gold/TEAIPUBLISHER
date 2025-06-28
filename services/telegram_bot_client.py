"""
Bot-based Telegram Client for channel management using bot token
"""
import asyncio
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class BotChannelInfo:
    """Channel information retrieved via Bot API"""
    id: int
    title: str
    username: Optional[str]
    type: str
    description: Optional[str]
    invite_link: Optional[str]
    member_count: Optional[int]
    permissions: Dict[str, Any]
    is_verified: bool = False
    is_scam: bool = False


class TelegramBotClient:
    """Telegram Bot API client for channel management"""
    
    def __init__(self, bot_token: str):
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
                logger.error(f"Bot API error: {data.get('description')}")
                return None
                
        except Exception as e:
            logger.error(f"Request error for {method}: {e}")
            return None
    
    def get_chat_info(self, chat_id: str) -> Optional[BotChannelInfo]:
        """Get chat information by ID using Bot API"""
        try:
            # Clean chat ID (remove @ if present)
            if chat_id.startswith('@'):
                chat_id = chat_id[1:]
            elif chat_id.startswith('-100'):
                # This is already a proper chat ID
                pass
            elif chat_id.isdigit():
                # Convert to proper format for supergroups/channels
                chat_id = f"-100{chat_id}"
            
            result = self._make_request('getChat', {'chat_id': chat_id})
            if not result:
                return None
            
            # Parse chat type
            chat_type = result.get('type', 'unknown')
            if chat_type == 'supergroup':
                chat_type = 'supergroup'
            elif chat_type == 'channel':
                chat_type = 'channel'
            elif chat_type == 'group':
                chat_type = 'group'
            
            # Get member count
            member_count = None
            try:
                count_result = self._make_request('getChatMemberCount', {'chat_id': chat_id})
                if count_result:
                    member_count = count_result
            except:
                pass
            
            # Get permissions
            permissions = {}
            if 'permissions' in result:
                perms = result['permissions']
                permissions = {
                    'can_send_messages': perms.get('can_send_messages', False),
                    'can_send_media_messages': perms.get('can_send_media_messages', False),
                    'can_send_polls': perms.get('can_send_polls', False),
                    'can_send_other_messages': perms.get('can_send_other_messages', False),
                    'can_add_web_page_previews': perms.get('can_add_web_page_previews', False),
                    'can_change_info': perms.get('can_change_info', False),
                    'can_invite_users': perms.get('can_invite_users', False),
                    'can_pin_messages': perms.get('can_pin_messages', False),
                }
            
            return BotChannelInfo(
                id=result.get('id'),
                title=result.get('title', 'Unknown'),
                username=result.get('username'),
                type=chat_type,
                description=result.get('description'),
                invite_link=result.get('invite_link'),
                member_count=member_count,
                permissions=permissions,
                is_verified=result.get('is_verified', False),
                is_scam=result.get('is_scam', False)
            )
            
        except Exception as e:
            logger.error(f"Error getting chat info for {chat_id}: {e}")
            return None
    
    def get_chat_administrators(self, chat_id: str) -> List[Dict]:
        """Get list of chat administrators"""
        try:
            result = self._make_request('getChatAdministrators', {'chat_id': chat_id})
            return result or []
        except Exception as e:
            logger.error(f"Error getting administrators for {chat_id}: {e}")
            return []
    
    def search_channels_by_ids(self, chat_ids: List[str]) -> List[BotChannelInfo]:
        """Search multiple channels by their IDs"""
        channels = []
        for chat_id in chat_ids:
            channel_info = self.get_chat_info(chat_id)
            if channel_info:
                channels.append(channel_info)
            # Add small delay to avoid rate limiting
            import time
            time.sleep(0.1)
        
        return channels
    
    def validate_bot_permissions(self, chat_id: str) -> Dict[str, bool]:
        """Check what permissions the bot has in a chat"""
        try:
            result = self._make_request('getChatMember', {
                'chat_id': chat_id,
                'user_id': self.get_bot_info()['id']
            })
            
            if not result:
                return {}
            
            status = result.get('status', 'member')
            permissions = {}
            
            if status in ['administrator', 'creator']:
                # Bot is admin, get admin rights
                if 'can_be_edited' in result:
                    permissions['can_be_edited'] = result.get('can_be_edited', False)
                if 'can_manage_chat' in result:
                    permissions['can_manage_chat'] = result.get('can_manage_chat', False)
                if 'can_change_info' in result:
                    permissions['can_change_info'] = result.get('can_change_info', False)
                if 'can_post_messages' in result:
                    permissions['can_post_messages'] = result.get('can_post_messages', False)
                if 'can_edit_messages' in result:
                    permissions['can_edit_messages'] = result.get('can_edit_messages', False)
                if 'can_delete_messages' in result:
                    permissions['can_delete_messages'] = result.get('can_delete_messages', False)
                if 'can_invite_users' in result:
                    permissions['can_invite_users'] = result.get('can_invite_users', False)
                if 'can_restrict_members' in result:
                    permissions['can_restrict_members'] = result.get('can_restrict_members', False)
                if 'can_pin_messages' in result:
                    permissions['can_pin_messages'] = result.get('can_pin_messages', False)
                if 'can_promote_members' in result:
                    permissions['can_promote_members'] = result.get('can_promote_members', False)
            
            permissions['status'] = status
            return permissions
            
        except Exception as e:
            logger.error(f"Error checking bot permissions for {chat_id}: {e}")
            return {}
    
    def get_bot_info(self) -> Dict:
        """Get information about the bot"""
        return self._make_request('getMe') or {}
    
    def test_connection(self) -> bool:
        """Test if bot token is valid"""
        try:
            result = self.get_bot_info()
            return bool(result and result.get('id'))
        except:
            return False
