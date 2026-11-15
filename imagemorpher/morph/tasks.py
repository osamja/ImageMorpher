import logging
import os
import time
import uuid

import dramatiq
import requests
from PIL import Image

from .morph import getDetectedCorrespondingPoints, morph
from .models import Morph
from .utils.graphics import getCroppedImageFromPath

logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=0)
def processMorph(morph_id_str, push_token=None):

    morph_id = uuid.UUID(morph_id_str)
    morph_instance = Morph.objects.get(id=morph_id)

    isMorphSequence = morph_instance.is_morph_sequence
    stepSize = morph_instance.step_size
    img1_path = morph_instance.first_image_ref
    img2_path = morph_instance.second_image_ref
    morphSequenceTime = morph_instance.morph_sequence_time
    morph_uri = morph_instance.morphed_image_ref
    morph_filepath = morph_instance.morphed_image_filepath
    duration = morph_instance.duration

    morph_instance.status = 'processing'
    morph_instance.progress = 0
    morph_instance.save()

    started_at = time.perf_counter()

    try:
        img1 = getCroppedImageFromPath(img1_path)
        img2 = getCroppedImageFromPath(img2_path)

        # Face detection is deterministic for a fixed image. Do it once per
        # job instead of once per frame, and reuse the resulting landmarks for
        # every t in the sequence.
        detection_started_at = time.perf_counter()
        img1_landmarks = getDetectedCorrespondingPoints(img1)
        img2_landmarks = getDetectedCorrespondingPoints(img2)
        detection_seconds = time.perf_counter() - detection_started_at

        if (isMorphSequence):
            # Keep the encoded frames in memory. The old implementation wrote
            # each JPEG and immediately reopened it to build the GIF.
            morphed_im_list = []

            total_frames = len(range(0, 101, stepSize))
            for frame_index, i in enumerate(range(0, 101, stepSize)):
                t = float(i / 100) or 0
                morphed_img_filename, morphed_im = morph(
                    img1,
                    img2,
                    t,
                    landmarks1=img1_landmarks,
                    landmarks2=img2_landmarks,
                )
                morphed_im_list.append(Image.fromarray(morphed_im))
                morph_instance.intermediate_images.append(morphed_img_filename)
                morph_instance.progress = int((frame_index + 1) / total_frames * 100)
                morph_instance.save()

            gif_frames = _prepare_gif_frames(morphed_im_list)
            gif_frames[0].save(
                morph_filepath,
                save_all=True,
                append_images=gif_frames[1:],
                loop=0,
                duration=duration,
            )

            morph_instance.progress = 100
            morph_instance.status = 'completed'
            morph_instance.save()

            _send_push_notification(push_token, morph_uri)

            logger.info(
                'morph completed id=%s frames=%s detection=%.3fs total=%.3fs',
                morph_id_str,
                total_frames,
                detection_seconds,
                time.perf_counter() - started_at,
            )
            return morph_uri
        else:
            morph_filepath, _ = morph(
                img1,
                img2,
                morphSequenceTime,
                morph_filepath,
                landmarks1=img1_landmarks,
                landmarks2=img2_landmarks,
            )

            morph_instance.progress = 100
            morph_instance.status = 'completed'
            morph_instance.save()

            _send_push_notification(push_token, morph_uri)

            logger.info(
                'morph completed id=%s frames=1 detection=%.3fs total=%.3fs',
                morph_id_str,
                detection_seconds,
                time.perf_counter() - started_at,
            )
            return morph_uri
    except Exception:
        logger.exception('morph failed id=%s elapsed=%.3fs', morph_id_str, time.perf_counter() - started_at)
        morph_instance.status = 'failed'
        morph_instance.save()
        return None


def _prepare_gif_frames(frames):
    """Quantize once with the fast octree path instead of per-frame median cut.

    PIL's default GIF encoder builds an adaptive palette for every frame. That
    was ~13 s and ~12 MB for a 101-frame sequence. FASTOCTREE brings that to
    ~1.3 s and ~7 MB, with a small quality trade-off. Set
    ``MORPH_GIF_QUANTIZE=quality`` to use the old slow path.
    """
    if os.environ.get('MORPH_GIF_QUANTIZE', 'fast').lower() == 'quality':
        return frames
    return [frame.quantize(colors=256, method=Image.FASTOCTREE) for frame in frames]


def _send_push_notification(push_token, morph_uri):
    """Best-effort push notification; delivery failure must not fail a morph."""
    if not push_token:
        return
    try:
        send_message(push_token, 'Morph Complete', 'Your morph is ready!', morph_uri)
    except Exception:
        logger.exception('push notification failed for morph=%s', morph_uri)


def send_message(expo_token, title, body, url):
    message = {
        'to': expo_token,
        'title': title,
        'body': body,
        'data': {
            'url': url
        }
    }
    return requests.post('https://exp.host/--/api/v2/push/send', json=message)
