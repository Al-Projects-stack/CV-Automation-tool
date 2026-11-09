"""Render promo-story.html frame by frame in headless Edge and save a looping GIF.

Usage: python promo/gif_export.py promo/promo-story.html docs/promo.gif 12.5 360
(12.5 fps keeps every frame at exactly 80 ms, which GIF can store without drift.)
"""
import base64
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
FPS = float(sys.argv[3]) if len(sys.argv) > 3 else 12.5
WIDTH = int(sys.argv[4]) if len(sys.argv) > 4 else 360
SCRATCH = Path(tempfile.gettempdir()) / "apply-py-gif"
SCRATCH.mkdir(exist_ok=True)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

EXPORT_JS = """
<script>
(async () => {
  try {
    await Promise.all([
      document.fonts.load('800 40px Unbounded'), document.fonts.load('600 40px Unbounded'),
      document.fonts.load("400 20px 'JetBrains Mono'"), document.fonts.load("500 20px 'JetBrains Mono'"),
    ]);
  } catch (e) {}
  playing = false;
  const FPS = %s, OW = %d, OH = Math.round(OW * 16 / 9);
  const small = document.createElement('canvas');
  small.width = OW; small.height = OH;
  const sctx = small.getContext('2d');
  sctx.imageSmoothingQuality = 'high';
  const frames = [];
  for (let i = 0, n = Math.round(DURATION * FPS); i < n; i++) {
    render(i / FPS);
    sctx.drawImage(canvas, 0, 0, OW, OH);
    frames.push(small.toDataURL('image/png'));
  }
  const pre = document.createElement('pre');
  pre.id = 'frames';
  pre.textContent = frames.join('\\n');
  document.body.appendChild(pre);
})();
</script>
""" % (FPS, WIDTH)

html = SRC.read_text(encoding="utf-8")
assert html.count("</body>") == 1
export_page = SCRATCH / "export.html"
export_page.write_text(html.replace("</body>", EXPORT_JS + "</body>"), encoding="utf-8")

dom = subprocess.run(
    [EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--mute-audio",
     f"--user-data-dir={SCRATCH / 'edge-profile'}", "--virtual-time-budget=60000",
     "--dump-dom", export_page.as_uri()],
    capture_output=True, text=True, encoding="utf-8", timeout=600,
).stdout

pngs = re.findall(r"data:image/png;base64,([A-Za-z0-9+/=]+)", dom)
assert pngs, "no frames came back from the browser"
print(f"frames: {len(pngs)} at {FPS} fps, {WIDTH}px wide")

frames = [Image.open(io.BytesIO(base64.b64decode(p))).convert("RGB") for p in pngs]
pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=round(1000 / FPS), loop=0, optimize=True, disposal=1)
print(f"wrote {OUT} ({OUT.stat().st_size / 1_000_000:.1f} MB)")
