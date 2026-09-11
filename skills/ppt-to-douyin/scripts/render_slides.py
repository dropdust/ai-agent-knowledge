#!/usr/bin/env python3
"""Render each segment as a vertical 1080x1920 slide image for Douyin.

Reads segments.json, writes slides/01.png, 02.png, ... using Pillow + Noto CJK.
Customize colors in DEFAULT_PALETTE; font sizes/padding inside render_slide().
"""
import argparse
import json
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

DEFAULT_PALETTE = {
    "bg_top": "#1a1625",
    "bg_bottom": "#0f0d1a",
    "accent": "#7c5cff",
    "title": "#ffffff",
    "body": "#d8d4e6",
    "muted": "#8b87a0",
}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load_font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REGULAR
    for p in (path, FONT_REGULAR):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def vertical_gradient(w, h, top, bottom):
    base = Image.new("RGB", (1, h))
    tr, tg, tb = top
    br, bg, bb = bottom
    for y in range(h):
        t = y / (h - 1)
        base.putpixel((0, y), (
            int(tr + (br - tr) * t),
            int(tg + (bg - tg) * t),
            int(tb + (bb - tb) * t),
        ))
    return base.resize((w, h))


def wrap(draw, text, font, max_w):
    lines = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        cur = ""
        for ch in para:
            if draw.textlength(cur + ch, font=font) <= max_w:
                cur += ch
            else:
                lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines


def render_slide(seg, outpath, palette, total):
    img = vertical_gradient(W, H, hex2rgb(palette["bg_top"]), hex2rgb(palette["bg_bottom"]))
    draw = ImageDraw.Draw(img)

    # top accent bar
    draw.rectangle([0, 0, W, 12], fill=palette["accent"])

    PAD = 90

    # progress counter, top-right
    prog = f"{seg['index']:02d} / {total:02d}"
    f_prog = load_font(40)
    draw.text((W - PAD - draw.textlength(prog, font=f_prog), 70), prog,
              font=f_prog, fill=palette["muted"])

    # title
    y = 180
    f_title = load_font(84, bold=True)
    title = seg["title"] or (seg["bullets"][0] if seg["bullets"] else "")
    for line in wrap(draw, title, f_title, W - 2 * PAD):
        draw.text((PAD, y), line, font=f_title, fill=palette["title"])
        y += 110
    y += 40

    # accent underline
    draw.rectangle([PAD, y, PAD + 160, y + 10], fill=palette["accent"])
    y += 60

    # bullets
    f_body = load_font(54)
    body_bullets = seg["bullets"]
    if seg["title"] and body_bullets and body_bullets[0] == seg["title"]:
        body_bullets = body_bullets[1:]
    for b in body_bullets:
        if y > H - 240:
            break
        lines = wrap(draw, b, f_body, W - 2 * PAD - 80)
        draw.ellipse([PAD, y + 20, PAD + 22, y + 42], fill=palette["accent"])
        for line in lines:
            draw.text((PAD + 50, y), line, font=f_body, fill=palette["body"])
            y += 80
        y += 30

    img.save(outpath)
    return outpath


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("segments", help="path to segments.json")
    ap.add_argument("-o", "--outdir", default="slides")
    ap.add_argument("--palette", help="optional palette.json overriding DEFAULT_PALETTE keys")
    args = ap.parse_args()

    with open(args.segments, encoding="utf-8") as f:
        segments = json.load(f)["segments"]

    palette = dict(DEFAULT_PALETTE)
    if args.palette:
        with open(args.palette, encoding="utf-8") as f:
            palette.update(json.load(f))

    os.makedirs(args.outdir, exist_ok=True)
    total = len(segments)
    for seg in segments:
        out = os.path.join(args.outdir, f"{seg['index']:02d}.png")
        render_slide(seg, out, palette, total)
        print(f"  rendered {out}")
    print(f"Done -> {args.outdir}")


if __name__ == "__main__":
    main()
