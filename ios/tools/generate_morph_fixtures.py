import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import Delaunay

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "MorpherCore/Tests/MorpherCoreTests/Fixtures"
)

WIDTH = 32
HEIGHT = 32


def gradient_one():
    ys, xs = np.mgrid[0:HEIGHT, 0:WIDTH]
    red = (xs * 5 + ys * 3) % 256
    green = (xs * 2 + ys * 7) % 256
    blue = (xs * 11 + ys * 13) % 256
    return np.stack([red, green, blue], axis=-1).astype(np.uint8)


def gradient_two():
    ys, xs = np.mgrid[0:HEIGHT, 0:WIDTH]
    red = (255 - xs * 5 + ys * 2) % 256
    green = (xs * 3 + 255 - ys * 6) % 256
    blue = (xs * 9 + ys * 4 + 80) % 256
    return np.stack([red, green, blue], axis=-1).astype(np.uint8)


def landmark_points(dx, dy):
    points = [
        [0.0, 0.0],
        [0.0, float(HEIGHT)],
        [float(WIDTH), 0.0],
        [float(WIDTH), float(HEIGHT)],
    ]
    for y in (8.0, 16.0, 24.0):
        for x in (8.0, 16.0, 24.0):
            points.append([x + dx, y + dy])
    return np.asarray(points)


def get_tri_points(shape, triangulation):
    grid = np.asarray(
        [(x, y) for y in range(shape[0]) for x in range(shape[1])],
        np.uint32,
    )
    simplex_numbers = Delaunay.find_simplex(
        triangulation,
        grid[: len(grid) - 1],
    )
    return {
        index: grid[np.where(simplex_numbers == index)]
        for index in range(len(triangulation.simplices))
    }


def get_valid_sample_points(image, xs, ys):
    rows, columns = image.shape[:2]
    if len(xs) and max(xs) >= columns:
        xs = xs[np.where(xs < columns)[0]]
    if len(ys) and max(ys) >= rows:
        ys = ys[np.where(ys < rows)[0]]
    length = min(len(xs), len(ys))
    return xs[:length], ys[:length]


def get_inverse_transformations(source_points, triangulation):
    homogeneous = np.vstack(
        (source_points.T, np.ones(source_points.T.shape[1]))
    )
    transforms = []
    for simplex in triangulation.simplices:
        triangle_points = triangulation.points[simplex]
        source_triangle = homogeneous.T[simplex]
        triangle_points = np.vstack(
            (triangle_points.T, np.ones(triangle_points.T.shape[1]))
        ).T
        matrix = np.dot(triangle_points.T, np.linalg.pinv(source_triangle.T))
        transforms.append(np.linalg.pinv(matrix))
    return transforms


def warp(image, triangle_dict, transforms):
    output = np.zeros(image.shape, dtype=np.uint8)
    for index in range(len(triangle_dict)):
        points = np.vstack(
            (triangle_dict[index].T, np.ones(len(triangle_dict[index])))
        ).T
        warped = np.dot(transforms[index], points.T).T.astype(int)
        warped_x = warped.T[0]
        warped_y = warped.T[1]
        if len(warped_x) == 0 or len(warped_y) == 0:
            continue
        warped_x, warped_y = get_valid_sample_points(
            image,
            warped_x,
            warped_y,
        )
        colors = image[warped_y, warped_x]
        image_points = triangle_dict[index]
        image_x = image_points.T[0]
        image_y = image_points.T[1]
        image_x, image_y = get_valid_sample_points(
            output,
            image_x,
            image_y,
        )
        length = min(len(image_x), len(image_y), len(colors))
        output[image_y[:length], image_x[:length]] = colors[:length]
    return output


def dissolve(first, second, t):
    return np.add(
        ((1 - t) * first).astype(np.uint8),
        (t * second).astype(np.uint8),
    )


def morph(image1, image2, points1, points2, t):
    midpoints = (1 - t) * points1 + t * points2
    triangulation = Delaunay(midpoints)
    triangle_dict = get_tri_points(image1.shape[:2], triangulation)
    transforms1 = get_inverse_transformations(points1, triangulation)
    transforms2 = get_inverse_transformations(points2, triangulation)
    warped1 = warp(image1, triangle_dict, transforms1)
    warped2 = warp(image2, triangle_dict, transforms2)
    return dissolve(warped1, warped2, t)


def flat_rgba(image):
    alpha = np.full((*image.shape[:2], 1), 255, dtype=np.uint8)
    return np.concatenate([image, alpha], axis=-1).reshape(-1).tolist()


def main():
    image1 = gradient_one()
    image2 = gradient_two()
    points1 = landmark_points(0, 0)
    points2 = landmark_points(3, -2)

    cases = []
    for t in (0.25, 0.5, 0.75):
        expected = morph(image1, image2, points1, points2, t)
        cases.append({"t": t, "expected": flat_rgba(expected)})

    fixture = {
        "width": WIDTH,
        "height": HEIGHT,
        "image1": flat_rgba(image1),
        "image2": flat_rgba(image2),
        "points1": points1.tolist(),
        "points2": points2.tolist(),
        "cases": cases,
    }

    FIXTURES.mkdir(parents=True, exist_ok=True)
    path = FIXTURES / "morph_python_32.json"
    path.write_text(json.dumps(fixture, separators=(",", ":")) + "\n")
    print(f"wrote {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
