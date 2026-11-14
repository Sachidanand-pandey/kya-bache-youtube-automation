
"""Generate unique and entertaining Hindi children's stories using Groq."""

import os
import json
import re
import time
import random
from pathlib import Path
from datetime import date
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

# Different story worlds and adventures.
STORY_CATEGORIES = [
    "Magical adventure and mysterious objects",
    "Jungle adventure and animal friendship",
    "Underwater kingdom and sea creatures",
    "Space adventure and friendly aliens",
    "School adventure and funny discoveries",
    "Village adventure and clever children",
    "Mystery solving and hidden treasures",
    "Time travel and historical imagination",
    "Robots, inventions and science experiments",
    "Fantasy kingdom and magical creatures",
    "Nature adventure and saving animals",
    "Funny friendship and unexpected situations",
    "Mountain adventure and secret caves",
    "Talking animals and unusual mysteries",
    "Dream world and magical journeys",
]


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

        visual = ""

        if isinstance(scene, dict):
            visual = str(
                scene.get("visual_prompt", "")
            ).strip()

        scenes.append({
            "narration": narration,
            "visual_prompt": visual or
                f"Colorful children's cartoon illustration: {narration}"
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
        "topic": str(data.get("topic", "Adventure")).strip(),
        "plot_summary": str(
            data.get("plot_summary", "")
        ).strip(),
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

        if isinstance(history, list):
            return history

        return []

    except (json.JSONDecodeError, OSError):

        print("Warning: Could not read story history.")
        return []


def story_text(story):

    parts = [
        story.get("title", ""),
        story.get("character", ""),
        story.get("plot_summary", "")
    ]

    for scene in story.get("scenes", []):
        parts.append(scene_narration(scene))

    parts.append(story.get("moral", ""))

    return " ".join(parts)


def find_duplicate(story, history):

    new_title = story.get("title", "").strip().lower()
    new_text = story_text(story).lower()

    new_plot = str(
        story.get("plot_summary", "")
    ).strip().lower()

    for old_story in history:

        if not isinstance(old_story, dict):
            continue

        old_title = str(
            old_story.get("title", "")
        ).strip().lower()

        if new_title and new_title == old_title:
            return True

        old_plot = str(
            old_story.get("plot_summary", "")
        ).strip().lower()

        # Compare the actual plot, not only character names.
        if new_plot and old_plot:

            plot_similarity = SequenceMatcher(
                None, new_plot, old_plot
            ).ratio()

            if plot_similarity > 0.75:
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


def choose_daily_category(history):

    # Select a category based on the date.
    # Avoid categories used in recent stories.

    day_number = date.today().toordinal()

    start_index = day_number % len(STORY_CATEGORIES)

    recent_categories = [
        str(item.get("category", ""))
        for item in history[-7:]
        if isinstance(item, dict)
    ]

    for offset in range(len(STORY_CATEGORIES)):

        category = STORY_CATEGORIES[
            (start_index + offset) % len(STORY_CATEGORIES)
        ]

        if category not in recent_categories:
            return category

    return STORY_CATEGORIES[start_index]


def generate_with_groq(topic, previous_titles, history):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Check your .env file."
        )

    client = Groq(api_key=api_key)

    if topic:
        selected_category = topic
    else:
        selected_category = choose_daily_category(history)

    previous_text = (
        "\n".join(
            f"- {title}"
            for title in previous_titles[-30:]
        )
        if previous_titles
        else "No previous stories."
    )

    recent_plots = []

    for item in history[-15:]:

        if isinstance(item, dict):

            plot = item.get("plot_summary", "")

            if plot:
                recent_plots.append(f"- {plot}")

    previous_plot_text = (
        "\n".join(recent_plots)
        if recent_plots
        else "No previous plot summaries available."
    )

    prompt = f"""
You are a professional and creative Hindi children's story writer.

Create ONE completely original and exciting Hindi story.

TARGET AUDIENCE:
Children aged 5 to 10.

TODAY'S STORY CATEGORY:
{selected_category}

PREVIOUS STORY TITLES - DO NOT REUSE:
{previous_text}

PREVIOUS STORY PLOTS - DO NOT COPY:
{previous_plot_text}

IMPORTANT CREATIVE RULES:

1. Create a genuinely NEW story plot.
2. Do not simply change the character's name in an old story.
3. Do not reuse the same adventure with different animals.
4. Change the setting, problem, adventure and story solution.
5. Choose interesting characters such as:
   - Children
   - Animals
   - Birds
   - Robots
   - Friendly aliens
   - Magical creatures
   - Inventors
   - Unusual fantasy characters

6. Use different locations:
   - Jungle
   - School
   - Village
   - Underwater kingdom
   - Space
   - Magical forest
   - Mountains
   - Secret caves
   - Fantasy kingdoms

7. Start with an interesting hook in the first scene.
8. Introduce a mystery, challenge or exciting problem.
9. Build suspense and curiosity throughout the story.
10. Include funny or surprising moments.
11. Give the main character a clever way to solve the problem.
12. End with a satisfying and happy conclusion.
13. Include a meaningful moral in simple Hindi.
14. Write natural Hindi that children can easily understand.
15. Avoid religious themes, violence and frightening content.
16. Keep the same main character appearance in all 12 scenes.
17. Make each scene visually different and interesting.
18. Each scene should move the story forward.
19. Use colorful 2D cartoon visual prompts in English.
20. Avoid repetitive narration and unnecessary filler.

STORY STRUCTURE:

Scene 1: Interesting opening and story hook.
Scene 2: Introduce the main character and location.
Scene 3: Discover an unusual event or problem.
Scene 4: Start the adventure.
Scene 5: First challenge.
Scene 6: Unexpected discovery.
Scene 7: New problem or mystery.
Scene 8: Clever plan.
Scene 9: Important challenge.
Scene 10: Exciting solution.
Scene 11: Happy conclusion.
Scene 12: Final emotional moment and lesson.

The plot must be original, not a copy of any previous story.

Return ONLY valid JSON.

Use this exact structure:

{{
  "title": "Hindi story title",
  "character": "Main character description",
  "character_guide": "Detailed consistent character appearance",
  "topic": "{selected_category}",
  "plot_summary": "A short English summary explaining the unique plot and its central problem and solution.",
  "scenes": [
    {{
      "narration": "Hindi narration",
      "visual_prompt": "Detailed English cartoon image description"
    }}
  ],
  "moral": "Hindi moral lesson"
}}

IMPORTANT:
- Exactly 12 scene objects.
- No additional scenes.
- No Markdown.
- No text outside JSON.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a highly creative Hindi children's "
                    "story author. You create original plots, "
                    "interesting adventures and age-appropriate "
                    "stories. Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1.0,
        max_completion_tokens=7000
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Groq returned an empty response.")

    story = json.loads(clean_json_text(content))

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
                f"\nGenerating original Hindi story "
                f"{attempt}/{MAX_ATTEMPTS}"
            )

            story = generate_with_groq(
                topic,
                previous_titles,
                history
            )

            if find_duplicate(story, history):

                raise ValueError(
                    "Similar previous story detected. "
                    "Generating a different plot."
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

            print("\nNew story generated successfully!")
            print("Title:", story["title"])
            print("Category:", story["topic"])

            return story

        except Exception as error:

            last_error = error

            print(
                f"Attempt {attempt} failed: {error}"
            )

            if attempt < MAX_ATTEMPTS:

                wait_time = attempt * 10

                print(
                    f"Retrying after {wait_time} seconds..."
                )

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
        "character": story.get("character", ""),
        "category": story.get("topic", ""),
        "plot_summary": story.get("plot_summary", ""),
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

    print("Story history updated successfully.")
