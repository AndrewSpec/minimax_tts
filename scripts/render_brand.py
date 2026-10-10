"""Render the integration's original waveform icon (not an official MiniMax logo)."""

from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1] / "custom_components/minimax_tts/brand"
root.mkdir(exist_ok=True)
image = Image.new("RGBA", (1024, 1024))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((40, 40, 984, 984), radius=220, fill="#12243B")
for x, height in ((248, 180), (380, 380), (512, 570), (644, 380), (776, 180)):
    draw.rounded_rectangle(
        (x - 38, 512 - height // 2, x + 38, 512 + height // 2),
        radius=38,
        fill="#56D5CF",
    )
image.resize((256, 256), Image.Resampling.LANCZOS).save(root / "icon.png")
image.resize((512, 512), Image.Resampling.LANCZOS).save(root / "icon@2x.png")
