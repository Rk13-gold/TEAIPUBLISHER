import unittest
from services.telegram_service import TelegramService

class TestTelegramService(unittest.TestCase):

    def setUp(self):
        self.telegram_service = TelegramService()

    def test_send_message(self):
        response = self.telegram_service.send_message(chat_id='123456', text='Test message')
        self.assertTrue(response['ok'])
        self.assertIn('result', response)

    def test_send_image(self):
        response = self.telegram_service.send_image(chat_id='123456', image_path='path/to/image.jpg')
        self.assertTrue(response['ok'])
        self.assertIn('result', response)

    def test_send_message_invalid_chat_id(self):
        response = self.telegram_service.send_message(chat_id='invalid_id', text='Test message')
        self.assertFalse(response['ok'])
        self.assertIn('error_code', response)

    def test_send_image_invalid_path(self):
        response = self.telegram_service.send_image(chat_id='123456', image_path='invalid/path/to/image.jpg')
        self.assertFalse(response['ok'])
        self.assertIn('error_code', response)

if __name__ == '__main__':
    unittest.main()