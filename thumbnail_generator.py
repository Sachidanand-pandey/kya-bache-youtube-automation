from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def make_thumbnail(scene_image, title):
    image = Image.open(scene_image).convert("RGB").resize((1280, 720))
    image = image.filter(ImageFilter.GaussianBlur(1))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((35, 35, 1245, 220), radius=35, fill=(5, 25, 45, 205))

    candidates = [
        "C:/Windows/Fonts/mangal.ttf",
        "C:/Windows/Fonts/Nirmala.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    font = ImageFont.load_default()
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                font = ImageFont.truetype(candidate, 62)
                break
            except OSError:
                pass

    draw.text((75, 85), title[:35], font=font, fill=(255, 240, 90, 255),
              stroke_width=3, stroke_fill=(20, 20, 20, 255))
    path = Path("output/thumbnail.jpg")
    image.save(path, quality=94)
    return path
