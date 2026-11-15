import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import Delaunay

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "MorpherCore/Tests/MorpherCoreTests/Fixtures"
)


def case(name, points):
    triangulation = Delaunay(points)
    simplices = sorted(
        sorted(int(index) for index in simplex)
        for simplex in triangulation.simplices
    )
    return {
        "name": name,
        "points": [[float(x), float(y)] for x, y in points],
        "simplices": simplices,
    }


def random_case(seed, count, high=500.0):
    rng = np.random.default_rng(seed)
    points = rng.uniform(0.0, high, size=(count, 2))
    return case(f"uniform-{count}-seed-{seed}", points)


def main():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    cases = {
        "delaunay_uniform_20.json": random_case(11, 20),
        "delaunay_uniform_73.json": random_case(7, 73),
        "delaunay_uniform_200.json": random_case(13, 200),
    }
    for filename, fixture in cases.items():
        path = FIXTURES / filename
        path.write_text(json.dumps(fixture, indent=2) + "\n")
        print(f"{filename}: {len(fixture['simplices'])} triangles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
