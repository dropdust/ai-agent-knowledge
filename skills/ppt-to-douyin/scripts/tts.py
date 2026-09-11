#!/usr/bin/env python3
"""Generate one mp3 per segment narration using edge-tts (free, no API key).

Chinese voices: xiaoxiao(女-亲切) xiaoyi(女-活泼) yunxi(男-新闻) yunjian(男-磁性)
yunyang(男-讲述).  rate like "+0%", "-10%", "+20%".
"""
import argparse
import asyncio
import json
import os

import edge_tts

VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi": "zh-CN-XiaoyiNeural",
    "yunxi": "zh-CN-YunxiNeural",
    "yunjian": "zh-CN-YunjianNeural",
    "yunyang": "zh-CN-YunyangNeural",
}


async def synth(text, voice, rate, outpath, retries=5):
    last = None
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(outpath)
            return
        except edge_tts.exceptions.NoAudioReceived as e:
            # edge-tts rate-limits intermittently; back off and retry
            last = e
            await asyncio.sleep(1.5 * (attempt + 1))
    raise last


async def run(segments, voice, rate, outdir):
    os.makedirs(outdir, exist_ok=True)
    for seg in segments:
        out = os.path.join(outdir, f"{seg['index']:02d}.mp3")
        print(f"  [{seg['index']:02d}] {seg['narration'][:40]}...")
        await synth(seg["narration"], voice, rate, out)
    print(f"Done -> {outdir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("segments", help="path to segments.json")
    ap.add_argument("-o", "--outdir", default="audio")
    ap.add_argument("--voice", default="xiaoxiao",
                    choices=sorted(VOICES) + sorted(VOICES.values()))
    ap.add_argument("--rate", default="+0%")
    args = ap.parse_args()

    with open(args.segments, encoding="utf-8") as f:
        segments = json.load(f)["segments"]

    voice = VOICES.get(args.voice, args.voice)
    asyncio.run(run(segments, voice, args.rate, args.outdir))


if __name__ == "__main__":
    main()
