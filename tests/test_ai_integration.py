import unittest
from ai_integration.lm_studio_client import LMStudioClient

class TestAIIntegration(unittest.TestCase):

    def setUp(self):
        self.client = LMStudioClient(api_key="test_api_key")

    def test_generate_content_success(self):
        title = "Test Title"
        image_description = "A beautiful sunset over the mountains."
        prompt = f"{title}: {image_description}"
        
        response = self.client.generate_content(prompt)
        
        self.assertIsNotNone(response)
        self.assertIn("generated_text", response)

    def test_generate_content_failure(self):
        title = "Test Title"
        image_description = ""
        prompt = f"{title}: {image_description}"
        
        with self.assertRaises(ValueError):
            self.client.generate_content(prompt)

    def test_api_key_validation(self):
        invalid_client = LMStudioClient(api_key="")
        with self.assertRaises(ValueError):
            invalid_client.validate_api_key()

if __name__ == '__main__':
    unittest.main()