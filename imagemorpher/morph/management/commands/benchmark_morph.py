import resource
import time

import cv2
import numpy as np
from autocrop import Cropper
from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from morph.morph import morph_frame
from morph.utils.detection import get_corresponding_points
from morph.utils.graphics import getImageReadyForCrop

DEFAULT_IMAGES = [
    'morph/tests/content/input/face-1.jpeg',
    'morph/tests/content/input/face-2.jpeg',
]


def _crop_to_face(path):
    img = Image.open(path)
    img = getImageReadyForCrop(img)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cropped = Cropper().crop(img_bgr).image
    if cropped is None:
        raise CommandError(f'Could not detect a face in {path}')
    return cropped


class Command(BaseCommand):
    help = 'Benchmark the morph pipeline without writing output files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--frames',
            default='1,6,101',
            help='Comma-separated frame counts (default: 1,6,101).',
        )
        parser.add_argument(
            '--repeat',
            type=int,
            default=3,
            help='Number of timed runs per configuration (default: 3).',
        )
        parser.add_argument(
            '--warp',
            choices=['legacy', 'vectorized', 'both'],
            default='vectorized',
            help='Warp implementation to benchmark (default: vectorized).',
        )
        parser.add_argument(
            '--images',
            nargs=2,
            default=DEFAULT_IMAGES,
            metavar=('IMAGE_1', 'IMAGE_2'),
            help='Two input images to morph.',
        )

    def handle(self, *args, **options):
        frame_counts = []
        for value in options['frames'].split(','):
            value = value.strip()
            if not value:
                continue
            count = int(value)
            if count < 1:
                raise CommandError('Frame counts must be positive')
            frame_counts.append(count)

        implementations = ['legacy', 'vectorized'] if options['warp'] == 'both' else [options['warp']]
        repeat = max(1, options['repeat'])

        crop_started_at = time.perf_counter()
        img1 = _crop_to_face(options['images'][0])
        img2 = _crop_to_face(options['images'][1])
        crop_seconds = time.perf_counter() - crop_started_at

        detection_started_at = time.perf_counter()
        landmarks1 = get_corresponding_points(img1)
        landmarks2 = get_corresponding_points(img2)
        detection_seconds = time.perf_counter() - detection_started_at

        self.stdout.write(
            f'inputs={img1.shape[1]}x{img1.shape[0]} '
            f'crop={crop_seconds:.3f}s detect={detection_seconds:.3f}s '
            f'peak_rss={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.1f}MB'
        )
        self.stdout.write('')
        self.stdout.write(f'{"frames":>8}  {"warp":>10}  {"mean_s":>10}  {"min_s":>10}  {"fps":>8}')

        # Warm up the caches so the reported numbers are steady-state.
        morph_frame(img1, img2, 0.5, landmarks1, landmarks2, warp_impl=implementations[0])

        for frame_count in frame_counts:
            timestamps = [0.5] if frame_count == 1 else np.linspace(0.0, 1.0, frame_count)
            for implementation in implementations:
                durations = []
                for _ in range(repeat):
                    started_at = time.perf_counter()
                    for t in timestamps:
                        morph_frame(
                            img1,
                            img2,
                            float(t),
                            landmarks1,
                            landmarks2,
                            warp_impl=implementation,
                        )
                    durations.append(time.perf_counter() - started_at)

                mean_seconds = sum(durations) / len(durations)
                min_seconds = min(durations)
                fps = frame_count / mean_seconds if mean_seconds else 0.0
                self.stdout.write(
                    f'{frame_count:>8}  {implementation:>10}  {mean_seconds:>10.3f}  '
                    f'{min_seconds:>10.3f}  {fps:>8.1f}'
                )

        self.stdout.write('')
        self.stdout.write(
            f'peak_rss={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.1f}MB'
        )
