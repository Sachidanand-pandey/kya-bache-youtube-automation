
"""Generate original Hindi children's stories using Gemini."""

import os
import json
import re
import time
from pathlib import Path
from difflib import SequenceMatcher

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
STORY_FILE = OUTPUT_DIR / "story.json"
HISTORY_FILE = OUTPUT_DIR / "story_history.json"

SCENE_COUNT = 12
MAX_ATTEMPTS = 1


def clean_json_text(text):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    return text.strip()


def scene_narration(scene):
    if isinstance(scene, str):
        return scene.strip()

    if isinstance(scene, dict):
        return str(scene.get("narration", "")).strip()

    return ""


def validate_story(data):

    if not isinstance(data, dict):
        raise ValueError("Invalid story format.")

    if not data.get("title"):
        raise ValueError("Story title is missing.")

    if not isinstance(data.get("scenes"), list):
        raise ValueError("Scenes must be a list.")

    if len(data["scenes"]) != SCENE_COUNT:
        raise ValueError("Story must contain exactly 12 scenes.")

    scenes = []

    for number, scene in enumerate(data["scenes"], 1):

        narration = scene_narration(scene)

        if not narration:
            raise ValueError(f"Narration missing in scene {number}")

        if isinstance(scene, dict):
            visual = str(
                scene.get("visual_prompt", "")
            ).strip()
        else:
            visual = ""

        scenes.append({
            "narration": narration,
            "visual_prompt": visual or
                f"Create a cartoon illustration for: {narration}"
        })

    moral = str(data.get("moral", "")).strip()

    if not moral:
        raise ValueError("Story moral is missing.")

    character = str(data.get("character", "Main character")).strip()

    return {
        "title": str(data["title"]).strip(),
        "character": character,
        "character_guide": str(
            data.get("character_guide", character)
        ).strip(),
        "topic": str(data.get("topic", "surprise")),
        "scenes": scenes,
        "moral": moral,
        "source": "gemini"
    }


def load_history():

    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        raise RuntimeError(
            "Story history is unreadable. Please check story_history.json."
        )


def story_text(story):

    narration = []

    for scene in story["scenes"]:
        narration.append(scene_narration(scene))

    return " ".join(
        [story["title"]] + narration + [story["moral"]]
    )


def find_duplicate(story, history):

    new_title = story["title"].lower()
    new_text = story_text(story).lower()

    for old in history:

        old_title = str(old.get("title", "")).lower()
        old_text = str(old.get("text", "")).lower()

        if old_title == new_title:
            return True

        if old_text:
            similarity = SequenceMatcher(
                None, new_text, old_text
            ).ratio()

            if similarity >= 0.82:
                return True

    return False


def generate_with_gemini(topic, previous_titles, attempt):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Check your .env file."
        )

    client = genai.Client(api_key=api_key)

    if topic:
        topic_instruction = (
            f"Create a children's story about: {topic}"
        )
    else:
        topic_instruction = """
Choose a fresh story idea yourself.

Rotate between:
- Animal stories
- Friendship
- School adventures
- Jungle adventures
- Magical stories
- Honesty
- Kindness
- Courage
- Family
- Nature
- Science adventures
- Indian folk-inspired fictional stories

Do not always generate the same type of story.
Do not force Bal Hanuman or religious stories unless requested.
"""

    previous = "\n".join(
        previous_titles[-50:]
    )

    prompt = f"""
You are an expert Hindi children's story writer.

Create an original and entertaining story for children
aged 5 to 10 years.

{topic_instruction}

LANGUAGE:
Use simple, natural Hindi in Devanagari script.

STORY REQUIREMENTS:
1. The story must be interesting and child-friendly.
2. It must have exactly 12 scenes.
3. Each scene must have 2 to 3 narration sentences.
4. The opening must attract children's attention.
5. Include a small problem or adventure.
6. The main character should solve the problem.
7. End with a happy and meaningful conclusion.
8. Include a positive moral.
9. Avoid frightening, graphic or harmful content.
10. Do not present fictional events as real history.

CHARACTER CONSISTENCY:
Describe the main character's appearance.
Keep the same appearance in all 12 illustrations.

IMAGE PROMPTS:
For every scene create a detailed English visual_prompt.
Describe the background, characters, action, lighting
and camera framing.

Image style:
Beautiful 2D cartoon storybook animation style.
Colorful, friendly and expressive characters.
Wide 16:9 composition.
No text, watermark or logo.

Return ONLY valid JSON.

Required format:

{{
  "title": "Hindi story title",
  "character": "Main character description",
  "character_guide": "Detailed consistent appearance",
  "topic": "Story category",
  "scenes": [
    {{
      "narration": "Hindi narration",
      "visual_prompt": "Detailed English image prompt"
    }}
  ],
  "moral": "Hindi moral"
}}

IMPORTANT:
- Exactly 12 scene objects.
- Do not add extra scenes.
- Do not repeat these previous titles:

{previous}

Generation attempt: {attempt}
"""

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    data = json.loads(
        clean_json_text(response.text)
    )

    story = validate_story(data)

    if topic:
        story["topic"] = topic

    return story


def generate_story(topic=""):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    history = load_history()

    previous_titles = [
        item.get("title", "")
        for item in history
    ]

    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:

            print(
                f"\nGenerating children's story "
                f"{attempt}/{MAX_ATTEMPTS}"
            )

            story = generate_with_gemini(
                topic,
                previous_titles,
                attempt
            )

            if find_duplicate(story, history):
                raise ValueError(
                    "Duplicate story detected. Trying another story."
                )

            with open(
                STORY_FILE, "w", encoding="utf-8"
            ) as file:

                json.dump(
                    story,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

            print("\nStory generated successfully!")
            print("Title:", story["title"])

            return story

        except Exception as error:

            last_error = error

            print(
                f"Attempt {attempt} failed: {error}"
            )

            if attempt < MAX_ATTEMPTS:
                time.sleep(min(attempt * 5, 30))

    raise RuntimeError(
        f"Story generation failed after {MAX_ATTEMPTS} attempts. "
        f"Last error: {last_error}"
    )


def record_successful_story(story):

    history = load_history()

    if find_duplicate(story, history):
        return

    history.append({
        "title": story["title"],
        "text": story_text(story)
    })

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        HISTORY_FILE, "w", encoding="utf-8"
    ) as file:

        json.dump(
            history[-365:],
            file,
            ensure_ascii=False,
            indent=4
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--topic",
        default="",
        help="Optional children's story topic"
    )

    args = parser.parse_args()

    story = generate_story(args.topic)

    print(
        json.dumps(
            story,
            ensure_ascii=False,
            indent=4
        )
    )

