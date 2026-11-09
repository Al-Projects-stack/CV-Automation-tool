"""Generate the promo voiceover with edge-tts and embed it in promo-story.html.

Usage: python promo/gen_voice.py promo/promo-story.html   (needs: pip install edge-tts)
The clips are base64-embedded between the VOICE-DATA markers so the page stays one file.
"""
import asyncio
import base64
import sys
import tempfile
from pathlib import Path

import edge_tts

OUT_JS = Path(sys.argv[1])
WORK = Path(tempfile.gettempdir()) / "apply-py-voice"

# Spoken text only; on-screen timing lives in promo-story.html (VOICE_LINES).
LINES = [
    "I sent the same CV to forty jobs.",
    "Most of them came back like this.",
    "Then I found one I actually wanted.",
    "And spent most of an hour on the first sentence.",
    "So I looked for something better.",
    "apply dot pie reads the job ad, and writes a CV and cover letter to match it.",
    "Three minutes later, I'd applied.",
    "This time, the replies were different.",
    "apply dot pie. It's free.",
]
VOICES = {"luke": "en-ZA-LukeNeural", "leah": "en-ZA-LeahNeural"}


async def main():
    packed = {}
    for key, voice in VOICES.items():
        clips = []
        for i, line in enumerate(LINES, 1):
            path = WORK / key / f"{i:02d}.mp3"
            path.parent.mkdir(parents=True, exist_ok=True)
            await edge_tts.Communicate(line, voice, rate="+0%").save(str(path))
            data = path.read_bytes()
            # Default output is 48 kbit/s mono MP3, so bytes -> seconds is a close estimate.
            print(f"{key} {i:02d}  ~{len(data) * 8 / 48000:4.1f}s  {line}")
            clips.append(base64.b64encode(data).decode("ascii"))
        packed[key] = clips

    # Embed between markers in the promo page so it stays one self-contained file.
    body = ",\n".join(f'  {k}: [\n' + ",\n".join(f'    "{c}"' for c in v) + "\n  ]" for k, v in packed.items())
    block = (
        "/* VOICE-DATA-START */\n"
        "// Voiceover clips generated with edge-tts (Microsoft neural voices, South African English).\n"
        "window.PROMO_VOICES = {\n" + body + "\n};\n"
        "/* VOICE-DATA-END */"
    )
    html = OUT_JS.read_text(encoding="utf-8")
    start, end = html.find("/* VOICE-DATA-START */"), html.find("/* VOICE-DATA-END */")
    assert html.count("/* VOICE-DATA-START */") == 1 and -1 < start < end, "voice markers missing"
    html = html[:start] + block + html[end + len("/* VOICE-DATA-END */"):]
    OUT_JS.write_text(html, encoding="utf-8")
    print(f"embedded voice into {OUT_JS} ({OUT_JS.stat().st_size // 1024} KB)")


asyncio.run(main())
