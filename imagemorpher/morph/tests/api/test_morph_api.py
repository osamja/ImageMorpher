import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from morph.models import Morph
import json


class MorphAPIIntegrationTest(TestCase):
    """
    Integration tests for the Morpher API endpoints
    """

    def setUp(self):
        """
        Set up test client and test data
        """
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_get_index_endpoint(self):
        """
        Test the GET /morph endpoint returns successfully
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'GET /morph')

    def test_morph_status_endpoint_with_valid_uuid(self):
        """
        Test that morph status endpoint returns correct data for existing morph
        """
        # Create a test morph instance
        morph_id = uuid.uuid4()
        morph = Morph.objects.create(
            id=morph_id,
            status='completed',
            first_image_ref='test_image1.jpg',
            second_image_ref='test_image2.jpg',
            morphed_image_ref='http://example.com/morph.jpg',
            morphed_image_filepath='/path/to/morph.jpg'
        )

        # Make request to status endpoint
        url = reverse('morph_status', kwargs={'morph_uuid': morph_id})
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['morphUri'], 'http://example.com/morph.jpg')

    def test_morph_status_endpoint_with_invalid_uuid(self):
        """
        Test that morph status endpoint returns 404 for non-existent morph
        """
        invalid_uuid = uuid.uuid4()
        url = reverse('morph_status', kwargs={'morph_uuid': invalid_uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_morph_creation_endpoint_without_images(self):
        """
        Test that morph endpoint returns 401 when no images are provided
        """
        response = self.client.post('/morph/morph', {})

        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid Request', str(response.data))

    def test_morph_creation_endpoint_with_mock_images(self):
        """
        Test that morph endpoint accepts valid request structure
        Note: This test uses mock image references rather than actual files
        """
        post_data = {
            'firstImageRef': 'test_image1.jpg',
            'secondImageRef': 'test_image2.jpg',
            'isAsync': 'True',
            'isSequence': 'False',
            'stepSize': '20',
            'duration': '250',
            't': '0.5',
            'clientId': 'test_client'
        }

        response = self.client.post('/morph/morph', post_data)

        # The endpoint should accept the request structure
        # In a real scenario, this would fail during processing due to missing actual files
        # but the request validation should pass
        self.assertIn(response.status_code, [200, 400])

    def test_get_user_morphs_unauthenticated(self):
        """
        Test that get_user_morphs endpoint requires authentication
        """
        response = self.client.get('/morph/mymorphs')

        # Should return 403 forbidden for unauthenticated requests
        self.assertEqual(response.status_code, 403)

    def test_log_client_error_endpoint(self):
        """
        Test that client error logging endpoint accepts POST requests
        """
        error_message = json.dumps({
            'error': 'Test error message',
            'timestamp': '2023-01-01T00:00:00Z'
        })

        response = self.client.post(
            '/morph/log',
            data=error_message,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

    def test_morph_status_transitions(self):
        """
        Test that morph status can transition through different states
        """
        morph_id = uuid.uuid4()
        morph = Morph.objects.create(
            id=morph_id,
            status='pending',
            first_image_ref='test1.jpg',
            second_image_ref='test2.jpg',
            morphed_image_ref='http://example.com/morph.jpg',
            morphed_image_filepath='/path/to/morph.jpg'
        )

        # Check initial status
        url = reverse('morph_status', kwargs={'morph_uuid': morph_id})
        response = self.client.get(url)
        self.assertEqual(response.json()['status'], 'pending')

        # Update status to processing
        morph.status = 'processing'
        morph.save()
        response = self.client.get(url)
        self.assertEqual(response.json()['status'], 'processing')

        # Update status to completed
        morph.status = 'completed'
        morph.save()
        response = self.client.get(url)
        self.assertEqual(response.json()['status'], 'completed')

    def test_morph_model_creation_with_defaults(self):
        """
        Test that Morph model creates correctly with default values
        """
        morph = Morph.objects.create(
            first_image_ref='image1.jpg',
            second_image_ref='image2.jpg',
            morphed_image_ref='morphed.jpg',
            morphed_image_filepath='/path/morphed.jpg'
        )

        self.assertEqual(morph.status, 'pending')
        self.assertEqual(morph.step_size, 20)
        self.assertEqual(morph.duration, 250)
        self.assertEqual(morph.morph_sequence_time, 0.5)
        self.assertEqual(morph.client_id, 'default')
        self.assertFalse(morph.is_morph_sequence)
