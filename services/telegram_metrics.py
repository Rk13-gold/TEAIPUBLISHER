from telethon.sync import TelegramClient

api_id = 28511289
api_hash = 'ff11a2ac8a96b6a91e0b843c51275628'

def get_channel_info(channel_username):
    with TelegramClient('session_name', api_id, api_hash) as client:
        channel = client.get_entity(channel_username)
        info = {
            "title": channel.title,
            "id": channel.id,
            "about": getattr(channel, "about", ""),
            "subscribers": getattr(channel, "participants_count", "N/A"),
        }
        return info

def get_last_posts(channel_username, limit=10):
    with TelegramClient('session_name', api_id, api_hash) as client:
        channel = client.get_entity(channel_username)
        posts = []
        for message in client.iter_messages(channel, limit=limit):
            posts.append({
                "text": message.text,
                "date": message.date,
                "views": message.views,
                "replies": message.replies.replies if message.replies else 0,
                "reactions": sum([r.count for r in message.reactions.results]) if message.reactions else 0,
            })
        return posts