
"""Generate original Hindi children's stories using Groq."""

import os
import json
import re
import time
from pathlib import Path
from difflib import SequenceMatcher

from dotenv import load_dotenv
from groq import Groq

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
STORY_FILE = OUTPUT_DIR / "story.json"
HISTORY_FILE = OUTPUT_DIR / "story_history.json"

SCENE_COUNT = 12
MAX_ATTEMPTS = 3

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


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
            raise ValueError(
                f"Narration missing in scene {number}"
            )

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

    character = str(
        data.get("character", "Main character")
    ).strip()

    return {
        "title": str(data["title"]).strip(),
        "character": character,
        "character_guide": str(
            data.get("character_guide", character)
        ).strip(),
        "topic": str(data.get("topic", "surprise")),
        "scenes": scenes,
        "moral": moral,
        "source": "groq"
    }


def load_history():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not HISTORY_FILE.exists():
        return []

    try:
        with open(
            HISTORY_FILE, "r", encoding="utf-8"
        ) as file:
            history = json.load(file)

        return history if isinstance(history, list) else []

    except (json.JSONDecodeError, OSError):
        print("Warning: Could not read story history.")
        return []


def story_text(story):

    parts = [story.get("title", "")]

    for scene in story.get("scenes", []):
        parts.append(scene_narration(scene))

    parts.append(story.get("moral", ""))

    return " ".join(parts)


def find_duplicate(story, history):

    new_text = story_text(story).lower()

    for old_story in history:

        old_title = str(
            old_story.get("title", "")
        ).strip().lower()

        new_title = story.get("title", "").strip().lower()

        if old_title and old_title == new_title:
            return True

        old_text = str(
            old_story.get("text", "")
        ).lower()

        if old_text:
            similarity = SequenceMatcher(
                None, new_text, old_text
            ).ratio()

            if similarity > 0.85:
                return True

    return False


def generate_with_groq(topic, previous_titles, attempt):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Check your .env file."
        )

    client = Groq(api_key=api_key)

    topic_text = topic if topic else "any interesting children's story"

    previous_text = (
        ", ".join(previous_titles[-20:])
        if previous_titles
        else "None"
    )

    prompt = f"""
Create one original Hindi children's story for children aged 5 to 10.

Topic: {topic_text}

Previously used story titles (avoid these):
{previous_text}

Requirements:
1. Write the complete story in simple, natural Hindi.
2. Create exactly 12 scenes.
3. Every scene must have narration and visual_prompt.
4. Keep the same main character throughout the story.
5. Make the story interesting, positive and suitable for children.
6. Include friendship, kindness, adventure or problem-solving.
7. Finish with a clear moral in Hindi.
8. Avoid religious themes and violence.
9. Make visual prompts suitable for colorful 2D cartoon illustrations.
10. Do not repeat previously used stories.

Return ONLY valid JSON in this exact structure:

{{
  "title": "Hindi story title",
  "character": "Main character description",
  "character_guide": "Detailed consistent character appearance",
  "topic": "{topic_text}",
  "scenes": [
    {{
      "narration": "Hindi narration",
      "visual_prompt": "English cartoon image description"
    }}
  ],
  "moral": "Hindi moral"
}}

There must be exactly 12 scene objects.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Hindi children's "
                    "story writer. Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8,
        max_completion_tokens=6000
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Groq returned an empty response.")

    cleaned = clean_json_text(content)

    story = json.loads(cleaned)

    return validate_story(story)


def generate_story(topic=""):

    history = load_history()

    previous_titles = [
        item.get("title", "")
        for item in history
        if isinstance(item, dict)
    ]

    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:

            print(
                f"\nGenerating children's story "
                f"{attempt}/{MAX_ATTEMPTS} using Groq"
            )

            story = generate_with_groq(
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
                wait_time = attempt * 10
                print(f"Retrying after {wait_time} seconds...")
                time.sleep(wait_time)

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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        HISTORY_FILE, "w", encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=4
        )
