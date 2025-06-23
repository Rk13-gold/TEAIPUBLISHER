import unittest
import sqlite3
from core.database import Database

class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = Database(':memory:')  # Use in-memory database for testing
        cls.db.create_tables()

    def test_insert_title(self):
        title = "Test Title"
        self.db.insert_title(title)
        result = self.db.fetch_titles()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], title)

    def test_insert_image(self):
        title_id = self.db.insert_title("Another Title")
        image_path = "path/to/image.jpg"
        self.db.insert_image(title_id, image_path, "keyword", "neutral")
        images = self.db.fetch_images_by_title_id(title_id)
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0][1], image_path)

    def test_associate_image_with_title(self):
        title_id = self.db.insert_title("Title for Association")
        image_id = self.db.insert_image(title_id, "image_path.jpg", "keyword", "neutral")
        self.db.associate_image_with_title(title_id, image_id)
        associations = self.db.fetch_images_by_title_id(title_id)
        self.assertIn(image_id, [img[0] for img in associations])

    def test_record_post(self):
        title_id = self.db.insert_title("Post Title")
        self.db.record_post(title_id, "This is a test post.")
        posts = self.db.fetch_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0][1], "This is a test post.")

    def test_user_event_logging(self):
        self.db.log_user_event("Test Event")
        events = self.db.fetch_user_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1], "Test Event")

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

if __name__ == '__main__':
    unittest.main()