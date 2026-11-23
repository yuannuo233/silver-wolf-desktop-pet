"""Remove a flat/similar background from a sprite image.

Flood-fills from every border pixel, erasing colors close to the border
color, then saves a transparent PNG. Useful for preparing AI-generated
sprite art (models usually output an opaque background).

Usage:
    python remove_background.py input.png [output.png] [tolerance]

tolerance (default 32): how different a pixel may be from the background
color and still be erased. Increase it for gradients/noisy backgrounds.
"""

import sys
from collections import deque
from pathlib import Path

from PIL import Image


def remove_background(input_path: str, output_path: str, tolerance: int = 32) -> None:
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size
    pixels = img.load()

    # reference background color = average of the four corners
    corners = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    ref = tuple(sum(c[i] for c in corners) // 4 for i in range(3))

    def is_background(px) -> bool:
        return (
            abs(px[0] - ref[0]) <= tolerance
            and abs(px[1] - ref[1]) <= tolerance
            and abs(px[2] - ref[2]) <= tolerance
        )

    # flood fill: start from all border pixels, erase connected background
    visited = [[False] * width for _ in range(height)]
    queue = deque()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if not (0 <= x < width and 0 <= y < height) or visited[y][x]:
            continue
        visited[y][x] = True
        if not is_background(pixels[x, y]):
            continue
        pixels[x, y] = (0, 0, 0, 0)  # make transparent
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    img.save(output_path)
    print(f"saved: {output_path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)
    inp = args[0]
    out = (
        args[1]
        if len(args) > 1
        else str(Path(inp).with_name(Path(inp).stem + "_transparent.png"))
    )
    tol = int(args[2]) if len(args) > 2 else 32
    remove_background(inp, out, tol)
