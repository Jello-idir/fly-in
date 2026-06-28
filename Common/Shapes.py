from PIL import Image
from enum import Enum


class Shapes(set[tuple[int, int, int]], Enum):
    @staticmethod
    def _load(path: str) -> set[tuple[int, int, int]]:
        img = Image.open(path).convert("RGBA")
        points = set()
        for y in range(img.height):
            for x in range(img.width):
                pixel = img.getpixel((x, y))
                if pixel[3] > 0:  # type: ignore
                    r, g, b, a = pixel  # type: ignore
                    color = (r << 24) + (g << 16) + (b << 8) + a
                    points.add((x, y, color))
        return points

    drone         = _load("Assets/drone.png")
    hub           = _load("Assets/hub.png")
    hub_restricted = _load("Assets/hub_restricted.png")
    hub_priority  = _load("Assets/hub_priority.png")
    hub_blocked   = _load("Assets/hub_blocked.png")
    hub_start     = _load("Assets/hub_start.png")

    def __call__(self):
        return self.value

    def _size(self):
        shape = self.value
        return max(p[0] for p in shape) + 1, max(p[1] for p in shape) + 1
