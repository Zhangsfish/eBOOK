"""Recreate the original icon with the already installed Pillow (not a CI dependency)."""
from pathlib import Path

from PIL import Image, ImageDraw

size = 3
image = Image.new("RGB", (1024 * size, 1024 * size), "#153E3B")
draw = ImageDraw.Draw(image)


def points(values):
    return [int(value * size) for value in values]


draw.rounded_rectangle(points((224, 194, 802, 830)), radius=36 * size, fill="#F6F0DF")
draw.rounded_rectangle(points((224, 194, 756, 790)), radius=32 * size, fill="#D1DECD")
draw.rectangle(points((224, 228, 290, 758)), fill="#96BBA8")
draw.line(points((292, 194, 292, 790)), fill="#153E3B", width=9 * size)
for y, right in [(344, 654), (434, 654), (524, 594)]:
    draw.rounded_rectangle(points((370, y, right, y + 20)), radius=10 * size, fill="#35605A")
draw.polygon([(590 * size, 194 * size), (662 * size, 194 * size),
              (662 * size, 314 * size), (626 * size, 286 * size),
              (590 * size, 314 * size)], fill="#B67650")
image = image.resize((1024, 1024), Image.Resampling.LANCZOS)
root = Path(__file__).resolve().parents[3]
target = root / "Sources/eBOOK/Assets.xcassets/AppIcon.appiconset/AppIcon.png"
image.save(target, optimize=True)
print("Wrote original opaque RGB icon:", target.relative_to(root))
