---
name: ppt-to-douyin
description: Turn PPT/text into a vertical Douyin video with voiceover.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [douyin, tiktok, video, ppt, tts, voiceover, 抖音, 口播, 视频]
    category: media
    related_skills: [powerpoint, pptx-cjk, piper-local-tts]
---

# ppt-to-douyin — PPT/文本 → 语音 → 抖音竖屏视频

把一份 `.pptx`（或纯文本）做成抖音竖屏口播视频：提取每页文字 → 逐页转语音 →
逐页渲染成 1080×1920 竖版画面 → ffmpeg 拼接成 MP4（可加背景音乐）。

## 何时使用

- 用户要把 PPT/讲义/知识卡片变成抖音视频（口播 + 幻灯片画面）。
- 用户说「读 PPT」「文本转语音」「生成抖音视频」「口播视频」等。

## 本机环境（已确认）

- ffmpeg 8.x ✓、uv ✓、Pillow ✓、Noto Sans CJK SC（常规+粗体）✓。
- **无 LibreOffice/soffice** —— 幻灯片画面不用 soffice 渲染，改用 PIL 直接画竖版
  （PPT 多是 16:9 横版，直接竖排到 9:16 更贴合抖音，画面也更可控）。
- python-pptx / edge-tts 用 `uv run --with` 临时拉取（系统无独立 pip）。
- edge-tts 直连可用（免 API key，无需代理）。

## 一键命令

```bash
uv run --with python-pptx --with edge-tts --with pillow \
  python3 ~/.hermes/skills/media/ppt-to-douyin/scripts/ppt_to_douyin.py \
  输入.pptx --voice xiaoxiao --bgm 背景音乐.mp3 -o 输出.mp4
```

产物：`输出.mp4`（1080×1920，H.264 + AAC，30fps）。中间文件 `segments.json`、
`slides/`、`audio/` 留在 `--workdir`（默认当前目录）。

### 常用参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--voice` | xiaoxiao | 中文音色（见下表），也接受完整 voice 名 |
| `--rate` | +0% | 语速，如 `-10%` `+20%` |
| `--bgm` | 无 | 背景音乐，循环混音 |
| `--bgm-volume` | 0.15 | BGM 音量 0~1 |
| `--tail` | 0.6 | 每页语音结束后停顿秒数 |
| `--include-notes` | 关 | 同时提取演讲者备注 |
| `--workdir` | . | 中间产物目录 |

### 中文音色（edge-tts）

| 名 | voice | 风格 |
|---|---|---|
| xiaoxiao | zh-CN-XiaoxiaoNeural | 女声，亲切自然（默认，适合科普口播） |
| xiaoyi | zh-CN-XiaoyiNeural | 女声，活泼 |
| yunxi | zh-CN-YunxiNeural | 男声，新闻播报 |
| yunjian | zh-CN-YunjianNeural | 男声，磁性 |
| yunyang | zh-CN-YunyangNeural | 男声，讲述/纪录片 |

## 分步执行（调试用）

四步脚本可单独跑，排查哪一步出问题：

```bash
SK=~/.hermes/skills/media/ppt-to-douyin/scripts
uv run --with python-pptx python3 $SK/ppt_extract.py 输入.pptx -o segments.json
uv run --with pillow        python3 $SK/render_slides.py segments.json -o slides
uv run --with edge-tts      python3 $SK/tts.py segments.json -o audio --voice xiaoxiao
python3 $SK/compose.py segments.json --slides slides --audio audio -o out.mp4
```

## 处理纯文本（无 PPT）

没有 PPT 时，直接用 python-pptx 之外的方式构造 `segments.json`（每段一个
`title` + `bullets`，`narration` 为要读出的完整口播文本），其余步骤不变。
脚本字段：`{"segments": [{"index":1, "title":"…", "bullets":[…], "narration":"…"}]}`。

## 用 Hermes 内置 TTS 工具替代（可选）

不想用 edge-tts 时，可用 `text_to_speech` 工具逐段生成音频（走 config.yaml 的
tts provider），再把 mp3 按 `audio/01.mp3`、`02.mp3`… 命名后跑 `compose.py`。
注意：本机 edge 默认 voice 是 `en-US-AriaNeural`（英文），中文内容需先把
config.yaml 的 `tts.edge.voice` 改成 `zh-CN-XiaoxiaoNeural` 之类，或直接用本
skill 的 edge-tts 脚本（推荐，音色可控且不碰全局配置）。

## 画面样式自定义

`render_slides.py` 顶部 `DEFAULT_PALETTE` 控制配色（bg_top/bg_bottom 渐变、
accent 强调色、title/body/muted 文字色、card）。改字号、内边距直接改
`render_slide()`。抖音竖屏 1080×1920，正文别超过 ~8 行，否则字号降到 54 以下。

## Pitfalls

- **narration 是读出文本，不等于屏幕 bullet 文本**：`ppt_extract.py` 把 title +
  bullets 用「。、」连接成口播句。标题里若含「1.」「•」等序号/符号，TTS 会逐字
  读出来，难听——提取后应先过一遍 narration，去掉序号、英文缩写、URL。
- **TTS 对每个 segment 独立调用**：跨页不要有必须连续才能听懂的半句话；每页
  narration 自成一个完整句子。
- **conat demuxer 要求各段参数一致**：`compose.py` 已统一 1080×1920、30fps、
  aac 44.1kHz，别手动改参数导致拼接失败。
- **edge-tts 偶发限流**：报 `NoAudioReceived` 是偶发的（非音色/文本问题），`tts.py` 已内置
  指数退避重试（5 次）。单页文字过长（>~400 字）更易触发，必要时给 narration 分句降速。
- **口播文本必须先清洗，不能直接读自动拼接的 narration**：PPT 页脚（每页重复的
  "XX 聚焦"、课程名）要先删；`● – · × → = + /` 等符号要规范成自然表达
  （`·`/`/`→`、`、`=`→`就是`、`+`→`加`、`→`→`，`、`7×24`→`7天24小时`）；
  **命令/URL 页（安装步骤、npx/curl 命令）要手写自然口播**，命令只留在画面不读。
  画面 bullets 保留原命令，narration 单独清洗（见本 skill 场景里的 clean 脚本思路）。
- **无 soffice**：不要尝试把 .pptx 转 PDF/PNG 来当画面；用本 skill 的 PIL 渲染
  （读的是提取后的文字，不是原样排版）。若用户坚持要原 PPT 排版，需另装
  LibreOffice。
- **BGM 音量**：默认 0.15 已偏低，人声清晰优先；别超过 0.3 否则盖过口播。
