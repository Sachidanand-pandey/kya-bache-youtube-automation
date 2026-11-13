
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGE_DIR = OUTPUT_DIR / "images"
THUMBNAIL_FILE = OUTPUT_DIR / "thumbnail.jpg"


def make_thumbnail(scene_image, title):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image = Image.open(scene_image).convert("RGB")
    image = image.resize((1280, 720))
    image = image.filter(ImageFilter.GaussianBlur(1))

    draw = ImageDraw.Draw(image, "RGBA")

    draw.rounded_rectangle(
        (35, 35, 1245, 220),
        radius=35,
        fill=(5, 25, 45, 205)
    )

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

    draw.text(
        (75, 85),
        str(title)[:35],
        font=font,
        fill=(255, 240, 90, 255),
        stroke_width=3,
        stroke_fill=(20, 20, 20, 255)
    )

    image.save(THUMBNAIL_FILE, quality=94)

    return THUMBNAIL_FILE


def create_thumbnail(story):
    first_scene_image = IMAGE_DIR / "scene_01.png"

    if not first_scene_image.exists():
        raise FileNotFoundError(
            f"First scene image not found: {first_scene_image}"
        )

    title = story.get("title", "Hindi Kids Story")

    return make_thumbnail(first_scene_image, title)
