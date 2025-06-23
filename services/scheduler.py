from datetime import datetime, timedelta
import threading
import time
import sqlite3
from core.database import Database
from services.telegram_service import TelegramService

class Scheduler:
    def __init__(self, db_path):
        self.db = Database(db_path)
        self.telegram_service = TelegramService()
        self.scheduled_posts = []

    def schedule_post(self, title_id, image_id, post_content, publish_time):
        if publish_time <= datetime.now():
            raise ValueError("Publish time must be in the future.")
        
        self.scheduled_posts.append({
            'title_id': title_id,
            'image_id': image_id,
            'content': post_content,
            'publish_time': publish_time
        })
        self.start_post_thread(title_id, image_id, post_content, publish_time)

    def start_post_thread(self, title_id, image_id, post_content, publish_time):
        delay = (publish_time - datetime.now()).total_seconds()
        threading.Timer(delay, self.publish_post, args=(title_id, image_id, post_content)).start()

    def publish_post(self, title_id, image_id, post_content):
        try:
            self.telegram_service.send_message(post_content)
            self.telegram_service.send_image(image_id)
            self.db.record_post(title_id, image_id, post_content, datetime.now())
        except Exception as e:
            print(f"Error publishing post: {e}")

    def get_scheduled_posts(self):
        return self.scheduled_posts

    def cancel_post(self, title_id):
        self.scheduled_posts = [post for post in self.scheduled_posts if post['title_id'] != title_id]