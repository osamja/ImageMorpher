import os
import uuid
from unittest import mock

import numpy as np
from django.test import SimpleTestCase, TestCase
from PIL import Image
from scipy.spatial import Delaunay

from morph.morph import morph_frame, warp_image
from morph.models import Morph
from morph.tasks import processMorph
from morph.utils import detection
from morph.utils.detection import get_corresponding_points
from morph.utils.image_sources import getMorphDirectory


def _landmark_grid(size=64):
    """Build 72 unique points (68 landmarks + 4 corners) for warp tests."""
    xs, ys = np.meshgrid(np.linspace(2, size - 2, 8), np.linspace(2, size - 2, 8))
    points = np.column_stack((xs.ravel(), ys.ravel()))
    extra = np.array([[size / 2, size / 2], [size / 2, 10], [10, size / 2], [size - 10, size / 2]])
    corners = np.array([[0, 0], [0, size], [size, 0], [size, size]])
    return np.vstack((points, extra, corners)).astype(np.float64)


class DetectionCacheTests(SimpleTestCase):
    def setUp(self):
        detection.reset_model_cache()

    def tearDown(self):
        detection.reset_model_cache()

    def test_detector_is_loaded_once(self):
        sentinel = object()
        with mock.patch.object(detection.dlib, 'get_frontal_face_detector', return_value=sentinel) as mocked:
            self.assertIs(detection.get_detector(), sentinel)
            self.assertIs(detection.get_detector(), sentinel)
            self.assertEqual(mocked.call_count, 1)

    def test_predictor_is_loaded_once(self):
        sentinel = object()
        with mock.patch.object(detection.dlib, 'shape_predictor', return_value=sentinel) as mocked:
            self.assertIs(detection.get_predictor(), sentinel)
            self.assertIs(detection.get_predictor(), sentinel)
            self.assertEqual(mocked.call_count, 1)

    def test_corner_order_matches_legacy(self):
        img = np.zeros((10, 20, 3), dtype=np.uint8)
        points = np.zeros((68, 2))
        result = detection.add_corner_points(img, points)
        np.testing.assert_array_equal(
            result[68:],
            np.array([[0, 0], [0, 10], [20, 0], [20, 10]]),
        )


class WarpTests(SimpleTestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        self.img = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
        self.points = _landmark_grid()
        self.triangulation = Delaunay(self.points)

    def test_identity_warp_reproduces_image(self):
        result = warp_image(self.img, self.points, self.points, self.triangulation.simplices)
        difference = np.abs(result.astype(np.int16) - self.img.astype(np.int16))
        self.assertLess(float(difference.mean()), 0.5)
        self.assertGreater(float((difference == 0).mean()), 0.99)

    def test_legacy_and_vectorized_warp_are_visually_close(self):
        from skimage.metrics import structural_similarity

        from morph.tests.correctness.test_morph_correctness import getFormattedImages

        img1, img2 = getFormattedImages(
            'morph/tests/content/input/face-1.jpeg',
            'morph/tests/content/input/face-2.jpeg',
        )
        points1 = get_corresponding_points(img1)
        points2 = get_corresponding_points(img2)

        legacy = morph_frame(img1, img2, 0.5, points1, points2, warp_impl='legacy')
        vectorized = morph_frame(img1, img2, 0.5, points1, points2, warp_impl='vectorized')

        similarity = structural_similarity(legacy, vectorized, channel_axis=2, data_range=255)
        self.assertGreater(float(similarity), 0.95)

    def test_morph_frame_uses_supplied_landmarks(self):
        with mock.patch(
            'morph.utils.detection.detect_face_landmarks',
            side_effect=AssertionError('morph_frame should not detect faces when landmarks are supplied'),
        ):
            frame = morph_frame(
                self.img,
                self.img,
                0.5,
                landmarks1=self.points,
                landmarks2=self.points,
            )
        self.assertEqual(frame.shape, self.img.shape)


class ProcessMorphDetectionTests(TestCase):
    def setUp(self):
        self.image_refs = []
        self.created_paths = []
        self.points = _landmark_grid()

        for _ in range(2):
            ref = f'test-{uuid.uuid4().hex}.jpg'
            path = getMorphDirectory() + ref
            Image.new('RGB', (64, 64), color=(120, 80, 40)).save(path)
            self.image_refs.append(ref)
            self.created_paths.append(path)

        self.gif_ref = f'test-{uuid.uuid4().hex}.gif'
        self.gif_path = getMorphDirectory() + self.gif_ref
        self.created_paths.append(self.gif_path)

        self.morph = Morph.objects.create(
            first_image_ref=self.image_refs[0],
            second_image_ref=self.image_refs[1],
            morphed_image_ref='http://example.com/test.gif',
            morphed_image_filepath=self.gif_path,
            is_morph_sequence=True,
            step_size=50,
        )

    def tearDown(self):
        for path in self.created_paths:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def test_sequence_detects_each_image_once(self):
        call_count = {'count': 0}

        def fake_detection(img):
            call_count['count'] += 1
            return self.points

        with mock.patch('morph.tasks.getDetectedCorrespondingPoints', side_effect=fake_detection):
            result = processMorph.fn(str(self.morph.id))

        self.morph.refresh_from_db()
        self.created_paths.extend(
            getMorphDirectory() + ref for ref in self.morph.intermediate_images
        )
        self.assertEqual(call_count['count'], 2)
        self.assertEqual(self.morph.status, 'completed')
        self.assertEqual(len(self.morph.intermediate_images), 3)
        self.assertIsNotNone(result)
