import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Import the FastAPI app
from app.main import app

client = TestClient(app)

class TestGenerateTopicMiscRoute(unittest.TestCase):

    @patch('app.db.operations.get_points_discussion_ids_by_topic_id', new_callable=AsyncMock)
    def test_generate_topic_misc_route_404(self, mock_get_points):
        # Set up the mock to return an empty list
        mock_get_points.return_value = []

        # Simulate a POST request to the endpoint
        response = client.post("/generate-topic-misc", json={"topic_id": "some_fake_id"})

        # Verify that the response is 404
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "No points of discussion found for this topic"})

    @patch('app.db.operations.get_points_discussion_ids_by_topic_id', new_callable=AsyncMock)
    def test_generate_topic_misc_route_success(self, mock_get_points):
        # Set up the mock to return a sample list
        mock_get_points.return_value = [
            {"id": "123", "point": "Sample point of discussion"}
        ]

        # Simulate a POST request to the endpoint
        response = client.post("/generate-topic-misc", json={"topic_id": "some_valid_id"})

        # Verify that the response is successful
        self.assertEqual(response.status_code, 200)
        # Further assertions can be added based on the expected output

if __name__ == '__main__':
    unittest.main()