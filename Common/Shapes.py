from PIL import Image
from enum import Enum


def load_shape_from_png(path: str) -> set[tuple[int, int, int]]:
    img = Image.open(path).convert("RGBA")
    points = set()
    for y in range(img.height):
        for x in range(img.width):
            pixel = img.getpixel((x, y))  # type: ignore
            if pixel[3] > 0:  # type: ignore
                r, g, b, a = pixel  # type: ignore
                color = (r << 24) + (g << 16) + (b << 8) + a
                points.add((x, y, color))
    return points


class Shapes(set[tuple[int, int, int]], Enum):
    def __call__(self):
        return self.value
    drone = load_shape_from_png("Assets/drone.png")
    hub = load_shape_from_png("Assets/hub.png")
    hub_restricted = load_shape_from_png("Assets/hub_restricted.png")
    hub_priority = load_shape_from_png("Assets/hub_priority.png")
    hub_blocked = load_shape_from_png("Assets/hub_blocked.png")
    hub_start = load_shape_from_png("Assets/hub_start.png")

    def _size(self):
        shape = self.value
        max_x = max(point[0] for point in shape)
        max_y = max(point[1] for point in shape)
        return max_x + 1, max_y + 1
