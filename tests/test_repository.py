import unittest
from data.repository import Repository
from core.database import Database

class TestRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database('test_database.db')
        cls.repo = Repository(cls.db)
        cls.db.create_tables()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_add_title(self):
        title = "Test Title"
        self.repo.add_title(title)
        titles = self.repo.get_titles()
        self.assertIn(title, titles)

    def test_add_image(self):
        title_id = self.repo.add_title("Another Title")
        image_path = "path/to/image.jpg"
        self.repo.add_image(image_path, title_id)
        images = self.repo.get_images_by_title_id(title_id)
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['path'], image_path)

    def test_associate_image_with_title(self):
        title_id = self.repo.add_title("Title for Association")
        image_id = self.repo.add_image("path/to/another_image.jpg", title_id)
        self.repo.associate_image_with_title(image_id, title_id)
        images = self.repo.get_images_by_title_id(title_id)
        self.assertIn(image_id, [img['id'] for img in images])

    def test_get_posts(self):
        self.repo.add_post("Test Post", "Content of the post")
        posts = self.repo.get_posts()
        self.assertGreater(len(posts), 0)

    def test_user_event_logging(self):
        self.repo.log_user_event("Test Event")
        events = self.repo.get_user_events()
        self.assertGreater(len(events), 0)

if __name__ == '__main__':
    unittest.main()