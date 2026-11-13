
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "output" / "images"

WIDTH = 1280
HEIGHT = 720

random.seed(10)


def draw_background(draw, scene_number):
    # Sky
    draw.rectangle((0, 0, WIDTH, 470), fill="#87CEEB")

    # Sun
    draw.ellipse((1030, 55, 1150, 175), fill="#FFD93D")

    # Clouds
    for x, y in [(150, 100), (450, 80), (780, 150)]:
        draw.ellipse((x, y, x + 100, y + 55), fill="white")
        draw.ellipse((x + 35, y - 25, x + 125, y + 55), fill="white")
        draw.ellipse((x + 70, y, x + 150, y + 55), fill="white")

    # Distant hills
    draw.ellipse((-150, 300, 600, 650), fill="#6DBB62")
    draw.ellipse((400, 300, 1100, 650), fill="#55A94F")
    draw.ellipse((850, 320, 1450, 650), fill="#70C56A")

    # Ground
    draw.rectangle((0, 460, WIDTH, HEIGHT), fill="#45A049")

    # Grass details
    for _ in range(150):
        x = random.randint(0, WIDTH)
        y = random.randint(470, HEIGHT)
        draw.line((x, y, x - 5, y - 15), fill="#277A36", width=3)

    # Trees
    for x, y in [(100, 330), (1080, 350), (900, 300)]:
        draw.rectangle((x, y, x + 35, y + 170), fill="#80552E")
        draw.ellipse((x - 60, y - 100, x + 100, y + 60),
                     fill="#238B45")
        draw.ellipse((x - 35, y - 140, x + 75, y + 20),
                     fill="#2E9E50")

    # Flowers
    for _ in range(35):
        x = random.randint(20, WIDTH - 20)
        y = random.randint(540, 690)
        color = random.choice(
            ["#FF69B4", "#FFFF00", "#FFFFFF", "#FF8C42"]
        )
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3),
                     fill="#F5C542")


def draw_rabbit(draw, x, y, scale=1):
    # Body
    draw.ellipse(
        (x - 65 * scale, y - 35 * scale,
         x + 65 * scale, y + 75 * scale),
        fill="#FFFFFF", outline="#555555", width=4
    )

    # Head
    draw.ellipse(
        (x - 65 * scale, y - 125 * scale,
         x + 65 * scale, y + 10 * scale),
        fill="#FFFFFF", outline="#555555", width=4
    )

    # Ears
    draw.ellipse(
        (x - 48 * scale, y - 235 * scale,
         x - 5 * scale, y - 90 * scale),
        fill="#FFFFFF", outline="#555555", width=4
    )
    draw.ellipse(
        (x + 5 * scale, y - 235 * scale,
         x + 48 * scale, y - 90 * scale),
        fill="#FFFFFF", outline="#555555", width=4
    )

    # Inner ears
    draw.ellipse(
        (x - 37 * scale, y - 215 * scale,
         x - 15 * scale, y - 105 * scale),
        fill="#FFB6C1"
    )
    draw.ellipse(
        (x + 15 * scale, y - 215 * scale,
         x + 37 * scale, y - 105 * scale),
        fill="#FFB6C1"
    )

    # Eyes and nose
    draw.ellipse(
        (x - 35 * scale, y - 75 * scale,
         x - 20 * scale, y - 58 * scale),
        fill="black"
    )
    draw.ellipse(
        (x + 20 * scale, y - 75 * scale,
         x + 35 * scale, y - 58 * scale),
        fill="black"
    )
    draw.ellipse(
        (x - 8 * scale, y - 43 * scale,
         x + 8 * scale, y - 31 * scale),
        fill="#FF69B4"
    )

    # Smile
    draw.arc(
        (x - 18 * scale, y - 45 * scale,
         x + 18 * scale, y - 15 * scale),
        0, 180, fill="black", width=3
    )

    # Blue scarf
    draw.rectangle(
        (x - 48 * scale, y - 5 * scale,
         x + 48 * scale, y + 15 * scale),
        fill="#168BFF"
    )
    draw.polygon(
        [(x + 35 * scale, y + 5 * scale),
         (x + 75 * scale, y + 35 * scale),
         (x + 35 * scale, y + 25 * scale)],
        fill="#168BFF"
    )


def draw_deer(draw, x, y, scale=1):
    # Body
    draw.ellipse(
        (x - 65 * scale, y - 20 * scale,
         x + 65 * scale, y + 75 * scale),
        fill="#B9783E", outline="#55351E", width=4
    )

    # Legs
    for lx in [-40, 35]:
        draw.rectangle(
            (x + lx * scale, y + 45 * scale,
             x + (lx + 15) * scale, y + 120 * scale),
            fill="#A96935"
        )

    # Neck and head
    draw.ellipse(
        (x + 20 * scale, y - 105 * scale,
         x + 90 * scale, y + 20 * scale),
        fill="#B9783E", outline="#55351E", width=3
    )
    draw.ellipse(
        (x + 35 * scale, y - 165 * scale,
         x + 125 * scale, y - 75 * scale),
        fill="#B9783E", outline="#55351E", width=3
    )

    # Ears
    draw.ellipse(
        (x + 5 * scale, y - 180 * scale,
         x + 55 * scale, y - 130 * scale),
        fill="#B9783E"
    )
    draw.ellipse(
        (x + 90 * scale, y - 185 * scale,
         x + 145 * scale, y - 135 * scale),
        fill="#B9783E"
    )

    # Eye and nose
    draw.ellipse(
        (x + 100 * scale, y - 130 * scale,
         x + 112 * scale, y - 118 * scale),
        fill="black"
    )
    draw.ellipse(
        (x + 115 * scale, y - 100 * scale,
         x + 130 * scale, y - 88 * scale),
        fill="#FF69B4"
    )

    # White spots
    for sx, sy in [(-35, 5), (-5, -5), (25, 15)]:
        draw.ellipse(
            (x + sx * scale, y + sy * scale,
             x + (sx + 13) * scale, y + (sy + 13) * scale),
            fill="white"
        )


def draw_lion(draw, x, y, scale=1):
    # Mane
    draw.ellipse(
        (x - 105 * scale, y - 190 * scale,
         x + 105 * scale, y + 40 * scale),
        fill="#A85C24", outline="#713C1A", width=5
    )

    # Face
    draw.ellipse(
        (x - 70 * scale, y - 155 * scale,
         x + 70 * scale, y - 15 * scale),
        fill="#F4B65E", outline="#713C1A", width=4
    )

    # Ears
    draw.ellipse(
        (x - 80 * scale, y - 160 * scale,
         x - 35 * scale, y - 115 * scale),
        fill="#F4B65E"
    )
    draw.ellipse(
        (x + 35 * scale, y - 160 * scale,
         x + 80 * scale, y - 115 * scale),
        fill="#F4B65E"
    )

    # Eyes
    draw.ellipse(
        (x - 40 * scale, y - 105 * scale,
         x - 22 * scale, y - 85 * scale),
        fill="black"
    )
    draw.ellipse(
        (x + 22 * scale, y - 105 * scale,
         x + 40 * scale, y - 85 * scale),
        fill="black"
    )

    # Nose and mouth
    draw.ellipse(
        (x - 12 * scale, y - 65 * scale,
         x + 12 * scale, y - 48 * scale),
        fill="#713C1A"
    )
    draw.arc(
        (x - 22 * scale, y - 65 * scale,
         x + 22 * scale, y - 25 * scale),
        0, 180, fill="black", width=4
    )

    # Body
    draw.ellipse(
        (x - 70 * scale, y - 15 * scale,
         x + 70 * scale, y + 100 * scale),
        fill="#F4B65E", outline="#713C1A", width=4
    )

    # Legs
    for lx in [-45, 35]:
        draw.rectangle(
            (x + lx * scale, y + 70 * scale,
             x + (lx + 25) * scale, y + 125 * scale),
            fill="#F4B65E"
        )


def draw_river(draw):
    draw.polygon(
        [(0, 500), (250, 475), (500, 530),
         (780, 490), (1050, 540), (1280, 500),
         (1280, 720), (0, 720)],
        fill="#31BDE8"
    )

    for y in [560, 620, 680]:
        draw.arc(
            (100, y, 500, y + 35),
            0, 180, fill="#FFFFFF", width=4
        )


def draw_ball(draw, x, y):
    draw.ellipse(
        (x - 45, y - 45, x + 45, y + 45),
        fill="#FF3030", outline="#9C1111", width=5
    )
    draw.arc(
        (x - 30, y - 30, x + 30, y + 30),
        0, 180, fill="white", width=5
    )


def create_scene_images(story, output_dir=None):
    scenes = story.get("scenes", [])

    if len(scenes) != 12:
        raise ValueError("Story must contain exactly 12 scenes.")

    target_dir = Path(output_dir) if output_dir else IMAGE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    image_paths = []

    for index, scene in enumerate(scenes, start=1):
        print(f"Creating cartoon image {index}/12...")

        image = Image.new(
            "RGB",
            (WIDTH, HEIGHT),
            "#87CEEB"
        )
        draw = ImageDraw.Draw(image)

        draw_background(draw, index)

        # River scenes
        if index in [9, 10, 11]:
            draw_river(draw)

        # Character positions
        if index == 1:
            draw_rabbit(draw, 640, 570, 1.35)

        elif index == 2:
            draw_rabbit(draw, 430, 570, 1.1)

        elif index == 3:
            draw_rabbit(draw, 450, 570, 0.9)
            draw_deer(draw, 750, 570, 0.9)

        elif index in [4, 5, 6]:
            draw_rabbit(draw, 330, 570, 0.8)
            draw_deer(draw, 600, 570, 0.8)
            draw_lion(draw, 900, 570, 0.8)

        elif index in [7, 8]:
            draw_rabbit(draw, 330, 570, 0.8)
            draw_deer(draw, 620, 570, 0.8)
            draw_lion(draw, 920, 570, 0.8)

        elif index == 9:
            draw_rabbit(draw, 330, 570, 0.8)
            draw_deer(draw, 620, 570, 0.8)
            draw_lion(draw, 920, 570, 0.8)
            draw_ball(draw, 1080, 520)

        elif index == 10:
            draw_rabbit(draw, 330, 570, 0.8)
            draw_deer(draw, 620, 570, 0.8)
            draw_lion(draw, 920, 570, 0.8)

            # Wooden bridge
            draw.rectangle(
                (400, 500, 850, 535),
                fill="#A66A35",
                outline="#633B1B",
                width=5
            )

        elif index == 11:
            draw_rabbit(draw, 330, 570, 0.8)
            draw_deer(draw, 620, 570, 0.8)
            draw_lion(draw, 920, 570, 0.8)
            draw_ball(draw, 800, 500)

        elif index == 12:
            draw_rabbit(draw, 330, 570, 0.8)
            draw_deer(draw, 620, 570, 0.8)
            draw_lion(draw, 920, 570, 0.8)

        image_path = target_dir / f"scene_{index:02d}.png"
        image.save(image_path, "PNG")

        image_paths.append(str(image_path))
        print("Saved:", image_path)

    print("\nAll 12 offline cartoon images created!")
    return image_paths
