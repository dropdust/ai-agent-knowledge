#!/usr/bin/env python3
"""Compose vertical slide images + narration audio into one Douyin MP4.

Inputs: segments.json, slides/NN.png, audio/NN.mp3.
Each segment lasts audio_duration + tail gap; concat all; optional BGM mix.
Output: 1080x1920, H.264 + AAC, 30fps, yuv420p (upload-ready).
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def compose(segments, slides_dir, audio_dir, out, tail, fps, bgm, bgm_volume, tempdir):
    seg_files = []
    for seg in segments:
        idx = seg["index"]
        img = os.path.join(slides_dir, f"{idx:02d}.png")
        aud = os.path.join(audio_dir, f"{idx:02d}.mp3")
        if not (os.path.exists(img) and os.path.exists(aud)):
            print(f"  skip {idx:02d}: missing {img} or {aud}")
            continue
        dur = ffprobe_duration(aud) + tail
        seg_out = os.path.join(tempdir, f"seg_{idx:02d}.mp4")
        run([
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(fps), "-t", f"{dur:.3f}", "-i", img,
            "-i", aud,
            "-c:v", "libx264", "-tune", "stillimage", "-r", str(fps),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-shortest", seg_out,
        ])
        seg_files.append(seg_out)

    if not seg_files:
        raise SystemExit("No segments produced -- check slides/ and audio/ dirs.")

    listfile = os.path.join(tempdir, "concat.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for s in seg_files:
            f.write(f"file '{s}'\n")

    if bgm:
        concat_out = os.path.join(tempdir, "concat.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
             "-c", "copy", concat_out])
        video_dur = ffprobe_duration(concat_out)
        run([
            "ffmpeg", "-y", "-i", concat_out,
            "-stream_loop", "-1", "-i", bgm,
            "-filter_complex",
            f"[1:a]volume={bgm_volume}[bg];"
            "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{video_dur:.3f}",
            out,
        ])
    else:
        # re-encode audio (not -c copy) to avoid Non-monotonic DTS from AAC priming
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("segments", help="path to segments.json")
    ap.add_argument("--slides", default="slides")
    ap.add_argument("--audio", default="audio")
    ap.add_argument("-o", "--output", default="douyin.mp4")
    ap.add_argument("--tail", type=float, default=0.6)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--bgm", help="background music file (looped, mixed under)")
    ap.add_argument("--bgm-volume", type=float, default=0.15)
    args = ap.parse_args()

    with open(args.segments, encoding="utf-8") as f:
        segments = json.load(f)["segments"]

    tempdir = tempfile.mkdtemp(prefix="douyin_")
    try:
        out = compose(segments, args.slides, args.audio, args.output,
                      args.tail, args.fps, args.bgm, args.bgm_volume, tempdir)
        print(f"\nDone: {out}")
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


if __name__ == "__main__":
    main()
