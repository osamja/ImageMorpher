"""Shared face detection and landmark helpers.

The dlib 68-point shape predictor is a 96 MB model. Constructing it is
expensive, so every process keeps a single instance instead of rebuilding it
for every image and every morph frame.

Dramatiq runs jobs on a thread pool and dlib's detector is not documented as
thread-safe, so calls into the detector/predictor are serialized with a lock.
Detection happens at most a couple of times per job, so the cost of
serializing it is negligible compared with reloading the model.
"""

import logging
import threading
from pathlib import Path

import dlib
import numpy as np

from morph.exceptions.FaceDetectException import FaceDetectException

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent / 'shape_predictor_68_face_landmarks.dat'
MODEL_LOCK = threading.RLock()

_detector = None
_predictor = None


def get_detector():
    """Return the process-wide dlib frontal face detector."""
    global _detector
    if _detector is None:
        with MODEL_LOCK:
            if _detector is None:
                _detector = dlib.get_frontal_face_detector()
    return _detector


def get_predictor():
    """Return the process-wide dlib 68-point shape predictor."""
    global _predictor
    if _predictor is None:
        with MODEL_LOCK:
            if _predictor is None:
                if not MODEL_PATH.exists():
                    raise FileNotFoundError(f'Missing dlib shape predictor: {MODEL_PATH}')
                _predictor = dlib.shape_predictor(str(MODEL_PATH))
    return _predictor


def reset_model_cache():
    """Drop cached models. Used by tests; not needed in normal operation."""
    global _detector, _predictor
    with MODEL_LOCK:
        _detector = None
        _predictor = None


def detect_faces(img, upsample=1):
    """Return dlib face rectangles for an image."""
    detector = get_detector()
    with MODEL_LOCK:
        return detector(img, upsample)


def detect_face_landmarks(img):
    """Detect the first face and return its 68 (x, y) landmarks.

    The old implementation silently used ``detector(img, 1)[0]``. We keep
    that behavior so output is unchanged while the model cache is warmed.
    """
    with MODEL_LOCK:
        faces = detect_faces(img)
        if len(faces) == 0:
            logger.error('Could not find corresponding points..')
            raise FaceDetectException('Could not find corresponding points..')

        face = faces[0]
        predictor = get_predictor()
        shape = predictor(img, face)

    points = np.array([(part.x, part.y) for part in shape.parts()], dtype=np.float64)
    if points.shape != (68, 2):
        raise FaceDetectException(
            f'Expected 68 landmarks, got {points.shape[0]}'
        )
    return points


def add_corner_points(img, points):
    """Append the four image corners in the legacy ordering.

    The resulting point array is ``68 + 4 = 72`` points. Keeping this order
    stable is important: source and destination point lists must line up.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.shape == (72, 2):
        return points
    if points.shape != (68, 2):
        raise ValueError(f'Expected 68 or 72 landmark points, got {points.shape}')

    height, width = img.shape[:2]
    corners = np.array(
        [
            [0, 0],
            [0, height],
            [width, 0],
            [width, height],
        ],
        dtype=np.float64,
    )
    return np.vstack((points, corners))


def get_corresponding_points(img):
    """Detect a face and return its 68 landmarks plus four corners."""
    return add_corner_points(img, detect_face_landmarks(img))


def ensure_corresponding_points(img, points=None):
    """Return a 72-point array, detecting landmarks only when needed."""
    if points is None:
        points = detect_face_landmarks(img)
    return add_corner_points(img, points)
