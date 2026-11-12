"""Generate a fresh, child-friendly Bal Hanuman Ji story using Gemini.

No offline story fallback is allowed: if Gemini fails or a duplicate is detected,
the program stops so the workflow cannot publish a repeated/ordinary story.
"""
import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path

OUTPUT_DIR = Path("output")
STORY_FILE = OUTPUT_DIR / "story.json"
HISTORY_FILE = OUTPUT_DIR / "story_history.json"
SCENE_COUNT = 12
MAX_ATTEMPTS = 4
MAX_HISTORY = 365
HANUMAN_TERMS = ("हनुमान", "बजरंगबली", "मारुति", "पवनपुत्र")


def clean_json_text(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def normalize(text):
    text = str(text).lower()
    return re.sub(r"[^\w\u0900-\u097f]+", "", text)


def validate_story(data):
    if not isinstance(data, dict):
        raise ValueError("Gemini response is not a JSON object.")
    for key in ("title", "character", "scenes", "moral"):
        if key not in data:
            raise ValueError(f"Missing story field: {key}")
    if not isinstance(data["scenes"], list) or len(data["scenes"]) != SCENE_COUNT:
        raise ValueError("Story must contain exactly 12 scenes.")

    scenes = [str(scene).strip() for scene in data["scenes"]]
    if any(not scene for scene in scenes):
        raise ValueError("Every scene must contain narration text.")
    for number, scene in enumerate(scenes, start=1):
        if not any(term in scene for term in HANUMAN_TERMS):
            raise ValueError(
                f"Scene {number} must explicitly mention Bal Hanuman Ji."
            )

    title = str(data["title"]).strip()
    character = str(data["character"]).strip()
    moral = str(data["moral"]).strip()
    if not title or not character or not moral:
        raise ValueError("Title, character and moral cannot be empty.")
    if not any(term in character for term in HANUMAN_TERMS):
        raise ValueError("The main character must be Bal Hanuman Ji.")

    result = {
        "title": title,
        "character": character,
        "scenes": scenes,
        "moral": moral,
    }
    if data.get("source"):
        result["source"] = str(data["source"])
    return result


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Story history must be a JSON list.")
        return data
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise RuntimeError(f"Cannot safely read story history: {exc}") from exc


def story_text(story):
    return " ".join([story["title"], *story["scenes"], story["moral"]])


def find_duplicate(story, history):
    new_title = normalize(story["title"])
    new_text = normalize(story_text(story))
    for old in history:
        old_title = normalize(old.get("title", ""))
        old_text = normalize(old.get("text", ""))
        if new_title and new_title == old_title:
            return old.get("title", "previous story")
        if old_text and SequenceMatcher(None, new_text, old_text).ratio() >= 0.78:
            return old.get("title", "previous story")
    return None


def generate_with_gemini(attempt, previous_titles):
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured. No story was generated.")

    client = genai.Client(api_key=api_key)
    title_list = "\n".join(f"- {title}" for title in previous_titles[-80:])
    prompt = f"""
Create a NEW, original Hindi devotional adventure story for children aged 4–9.
The central hero in every scene is बाल हनुमान जी (Bal Hanuman Ji).
Use gentle, respectful Hindu devotional storytelling and child-friendly language.
Themes may include courage, kindness, helping others, honesty, devotion and wisdom.
Do not copy or closely imitate any known story, scripture episode, movie, cartoon,
or any story in the previous-title list. Invent a fresh, simple child-safe situation.
Bal Hanuman Ji must actively participate in every scene. Every scene's narration
must explicitly include the words 'हनुमान जी' or 'बाल हनुमान'.
Return ONLY valid JSON, in Devanagari Hindi, with exactly these keys:
title, character, scenes, moral.
The scenes array must contain EXACTLY 12 non-empty scenes. Each scene should have
2–3 connected sentences suitable for Hindi voice narration. Include a clear opening,
a gentle problem, a thoughtful solution, a happy ending and a positive moral.
Avoid violence, frightening content, dangerous instructions and disrespectful content.
Attempt number: {attempt}. Create a different plot, not just different wording.
Previously used titles (avoid these):
{title_list if title_list else '- None yet'}
JSON shape: {{"title":"...", "character":"बाल हनुमान जी", "scenes":[12 strings], "moral":"..."}}
"""
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
    )
    if not getattr(response, "text", None):
        raise RuntimeError("Gemini returned an empty response.")
    return validate_story(json.loads(clean_json_text(response.text)))


def generate_story():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    history = load_history()
    previous_titles = [item.get("title", "") for item in history]
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            story = generate_with_gemini(attempt, previous_titles)
            duplicate_title = find_duplicate(story, history)
            if duplicate_title:
                raise ValueError(
                    f"Possible duplicate of previous story: {duplicate_title}"
                )

            story["source"] = "gemini"
            history.append({
                "title": story["title"],
                "text": story_text(story),
            })
            history = history[-MAX_HISTORY:]
            HISTORY_FILE.write_text(
                json.dumps(history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            STORY_FILE.write_text(
                json.dumps(story, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"New Bal Hanuman Ji story accepted on attempt {attempt}.")
            return story
        except Exception as exc:
            last_error = exc
            print(f"Story attempt {attempt}/{MAX_ATTEMPTS} rejected: {exc}")

    raise RuntimeError(
        f"STOP: Gemini did not produce a valid, sufficiently new Bal Hanuman Ji story "
        f"after {MAX_ATTEMPTS} attempts. Nothing should be uploaded. Last error: {last_error}"
    )


if __name__ == "__main__":
    print(json.dumps(generate_story(), ensure_ascii=False, indent=2))
