"""One-off script to regenerate landing/public/favicon.ico from the mirror mark.

Draws the same chevron "M" mark used in landing/src/components/mirror-shell.tsx
(MirrorMark) at high resolution, then downsamples for anti-aliasing, since PIL's
line drawing has no native anti-aliasing. Run again if the mark or brand colors
in landing/src/styles.css change.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BACKGROUND = (244, 234, 217)  # matches --background in landing/src/styles.css
INK = (58, 51, 46)  # matches --foreground

SUPERSAMPLE = 8
SIZES = [16, 32, 48, 64, 128, 256]


def draw_mark(size: int) -> Image.Image:
    scale = SUPERSAMPLE
    big = size * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([0, 0, big - 1, big - 1], fill=BACKGROUND + (255,))

    # Mark path (viewBox 0 0 48 40, translated/scaled to fit inside the circle).
    def pt(x: float, y: float) -> tuple[float, float]:
        # Fit the 48x40 mark into a centered ~62% of the circle.
        mark_scale = big * 0.62 / 48
        off_x = (big - 48 * mark_scale) / 2
        off_y = (big - 40 * mark_scale) / 2
        return (off_x + x * mark_scale, off_y + y * mark_scale)

    width = max(1, round(big * 3.4 / 64))
    draw.line([pt(5, 35), pt(5, 5), pt(24, 26), pt(43, 5), pt(43, 35)], fill=INK + (255,), width=width, joint="curve")
    draw.line([pt(24, 26), pt(43, 5), pt(43, 35)], fill=INK + (90,), width=width, joint="curve")

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    public_dir = Path(__file__).resolve().parent.parent / "landing" / "public"
    images = [draw_mark(size) for size in SIZES]
    images[0].save(public_dir / "favicon.ico", sizes=[(s, s) for s in SIZES])
    images[-1].save(public_dir / "apple-touch-icon.png")
    print(f"Wrote {public_dir / 'favicon.ico'} and apple-touch-icon.png")


if __name__ == "__main__":
    main()
