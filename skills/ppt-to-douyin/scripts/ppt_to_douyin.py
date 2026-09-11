#!/usr/bin/env python3
"""One-shot: .pptx -> Douyin vertical video (extract + render + TTS + compose).

Usage:
  uv run --with python-pptx --with edge-tts --with pillow \
    python3 ppt_to_douyin.py 输入.pptx --voice xiaoxiao -o out.mp4
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sh(args):
    print("$ " + " ".join(args))
    subprocess.run([sys.executable] + args, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="path to .pptx (or segments.json)")
    ap.add_argument("-o", "--output", default="douyin.mp4")
    ap.add_argument("--voice", default="xiaoxiao")
    ap.add_argument("--rate", default="+0%")
    ap.add_argument("--bgm", help="background music file")
    ap.add_argument("--bgm-volume", type=float, default=0.15)
    ap.add_argument("--tail", type=float, default=0.6)
    ap.add_argument("--include-notes", action="store_true")
    ap.add_argument("--workdir", default=".", help="dir for segments.json/slides/audio")
    args = ap.parse_args()

    wd = args.workdir
    os.makedirs(wd, exist_ok=True)
    seg = os.path.join(wd, "segments.json")
    slides = os.path.join(wd, "slides")
    audio = os.path.join(wd, "audio")

    if args.input.endswith(".json"):
        seg = args.input
    else:
        print("== 1/4 extract ==")
        cmd = [os.path.join(HERE, "ppt_extract.py"), args.input, "-o", seg]
        if args.include_notes:
            cmd.append("--include-notes")
        sh(cmd)

    print("== 2/4 render slides ==")
    sh([os.path.join(HERE, "render_slides.py"), seg, "-o", slides])

    print("== 3/4 TTS ==")
    sh([os.path.join(HERE, "tts.py"), seg, "-o", audio,
        "--voice", args.voice, "--rate", args.rate])

    print("== 4/4 compose ==")
    cmd = [os.path.join(HERE, "compose.py"), seg,
           "--slides", slides, "--audio", audio,
           "-o", args.output, "--tail", str(args.tail)]
    if args.bgm:
        cmd += ["--bgm", args.bgm, "--bgm-volume", str(args.bgm_volume)]
    sh(cmd)

    print(f"\nDone: {args.output}")


if __name__ == "__main__":
    main()
