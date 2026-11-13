
import json
from pathlib import Path
from image_generator import generate_one_image
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

with open("output/story.json", "r", encoding="utf-8") as file:
    story = json.load(file)

scene = story["scenes"][0]

image_data = generate_one_image(
    client,
    scene["visual_prompt"],
    story.get("character_guide", story.get("character", "")),
    1
)

Path("output/test_scene_01.png").write_bytes(image_data)

print("Test image generated successfully!")
