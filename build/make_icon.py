"""Generate app.ico for Sherlock GUI (magnifier on a blue rounded square)."""
import os
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "app.ico")
S = 256

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

d.rounded_rectangle((4, 4, S - 5, S - 5), radius=58, fill=(29, 78, 216, 255))
d.rounded_rectangle((4, 4, S - 5, 132), radius=58, fill=(37, 99, 235, 255))
d.rectangle((4, 100, S - 5, 132), fill=(37, 99, 235, 255))

cx, cy, r = 106, 104, 52
d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 255), width=16)
d.arc((cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14),
      start=195, end=285, fill=(191, 219, 254, 255), width=8)
d.line((cx + 38, cy + 38, 198, 196), fill=(255, 255, 255, 255), width=24)
d.ellipse((198 - 13, 196 - 13, 198 + 13, 196 + 13), fill=(255, 255, 255, 255))

img.save(OUT, format="ICO",
         sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote", OUT, os.path.getsize(OUT), "bytes")
