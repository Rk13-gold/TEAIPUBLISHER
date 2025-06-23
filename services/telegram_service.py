import requests
import json

class TelegramService:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id, text, buttons=None):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if buttons:
            keyboard = {
                "inline_keyboard": [
                    [{"text": btn["text"], "url": btn["url"]}] for btn in buttons
                ]
            }
            payload["reply_markup"] = keyboard
        response = requests.post(url, json=payload)
        print("Respuesta send_message:", response.json())  # <-- Muestra la respuesta de la API
        return response.json()

    def send_image(self, chat_id, image_path, caption=None, buttons=None):
        url = f"{self.base_url}/sendPhoto"
        data = {
            "chat_id": chat_id,
            "caption": caption or "",
            "parse_mode": "HTML"
        }
        if buttons:
            keyboard = {
                "inline_keyboard": [
                    [{"text": btn["text"], "url": btn["url"]}] for btn in buttons
                ]
            }
            data["reply_markup"] = json.dumps(keyboard)
        with open(image_path, "rb") as image_file:
            files = {"photo": image_file}
            response = requests.post(url, data=data, files=files)
        print("Respuesta send_image:", response.json())  # <-- Muestra la respuesta de la API
        return response.json()

    def send_post_sync(self, title, image_path, content, schedule_time, buttons, chat_id):
        if image_path:
            caption = f"<b>{title}</b>\n{content}"
            return self.send_image(chat_id, image_path, caption, buttons)
        else:
            text = f"<b>{title}</b>\n{content}"
            return self.send_message(chat_id, text, buttons)