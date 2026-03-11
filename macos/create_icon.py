"""Generate the prinzclaw menubar icon and app icon programmatically."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def _create_png(width: int, height: int, pixels: list[list[tuple[int, int, int, int]]]) -> bytes:
    """Create a PNG file from RGBA pixel data."""

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))

    raw = b""
    for row in pixels:
        raw += b"\x00"  # Filter none
        for r, g, b, a in row:
            raw += struct.pack("BBBB", r, g, b, a)

    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")

    return header + ihdr + idat + iend


def create_menubar_icon(output_path: str) -> None:
    """Create a 22x22 menubar icon — red P on transparent background."""
    size = 22
    pixels = [[(0, 0, 0, 0)] * size for _ in range(size)]

    # Draw a bold "P" shape in red (#e63946)
    red = (230, 57, 70, 255)

    # Vertical bar of P (x=5..8, y=3..18)
    for y in range(3, 19):
        for x in range(5, 9):
            pixels[y][x] = red

    # Top horizontal of P (x=5..15, y=3..6)
    for y in range(3, 7):
        for x in range(5, 16):
            pixels[y][x] = red

    # Right curve of P (x=13..16, y=5..12)
    for y in range(5, 13):
        for x in range(13, 17):
            pixels[y][x] = red

    # Bottom horizontal of P bowl (x=5..15, y=10..13)
    for y in range(10, 14):
        for x in range(5, 16):
            pixels[y][x] = red

    # Smooth corners slightly
    pixels[3][5] = (0, 0, 0, 0)
    pixels[3][15] = (0, 0, 0, 0)
    pixels[13][15] = (0, 0, 0, 0)

    png_data = _create_png(size, size, pixels)
    Path(output_path).write_bytes(png_data)


def create_app_icon(output_path: str) -> None:
    """Create a 256x256 app icon — red P on dark rounded square."""
    size = 256
    pixels = [[(0, 0, 0, 0)] * size for _ in range(size)]

    # Dark rounded square background
    bg = (20, 20, 20, 255)
    red = (230, 57, 70, 255)
    radius = 40

    for y in range(size):
        for x in range(size):
            # Rounded corners check
            in_rect = True
            if x < radius and y < radius:
                in_rect = (x - radius) ** 2 + (y - radius) ** 2 <= radius ** 2
            elif x >= size - radius and y < radius:
                in_rect = (x - (size - radius - 1)) ** 2 + (y - radius) ** 2 <= radius ** 2
            elif x < radius and y >= size - radius:
                in_rect = (x - radius) ** 2 + (y - (size - radius - 1)) ** 2 <= radius ** 2
            elif x >= size - radius and y >= size - radius:
                in_rect = (x - (size - radius - 1)) ** 2 + (y - (size - radius - 1)) ** 2 <= radius ** 2

            if in_rect:
                pixels[y][x] = bg

    # Draw P letter centered — vertical bar
    for y in range(50, 210):
        for x in range(60, 95):
            pixels[y][x] = red

    # Top horizontal
    for y in range(50, 85):
        for x in range(60, 175):
            pixels[y][x] = red

    # Right bump of P
    for y in range(70, 140):
        for x in range(155, 195):
            pixels[y][x] = red

    # Middle horizontal closing the P
    for y in range(120, 155):
        for x in range(60, 175):
            pixels[y][x] = red

    png_data = _create_png(size, size, pixels)
    Path(output_path).write_bytes(png_data)


def create_dmg_background(output_path: str) -> None:
    """Create a 600x400 DMG background image."""
    w, h = 600, 400
    pixels = [[(0, 0, 0, 0)] * w for _ in range(h)]

    # Dark background with subtle gradient
    for y in range(h):
        shade = int(10 + (y / h) * 12)
        for x in range(w):
            pixels[y][x] = (shade, shade, shade, 255)

    # Red accent line at top
    for y in range(0, 3):
        for x in range(w):
            pixels[y][x] = (230, 57, 70, 255)

    # Arrow area: draw a simple right arrow in the center (pointing from left to right)
    # Arrow body (y=195..205, x=220..380)
    arrow_color = (100, 100, 100, 200)
    for y in range(195, 206):
        for x in range(220, 380):
            pixels[y][x] = arrow_color

    # Arrow head (triangle pointing right at x=380)
    for dy in range(-20, 21):
        tip_x = 380 + (20 - abs(dy))
        for x in range(380, min(tip_x + 1, w)):
            if 0 <= 200 + dy < h:
                pixels[200 + dy][x] = arrow_color

    png_data = _create_png(w, h, pixels)
    Path(output_path).write_bytes(png_data)


if __name__ == "__main__":
    out = Path(__file__).parent / "resources"
    out.mkdir(exist_ok=True)
    create_menubar_icon(str(out / "icon.png"))
    create_app_icon(str(out / "app_icon.png"))
    create_dmg_background(str(out / "dmg_background.png"))
    print("Icons generated in", out)
