"""Small manual smoke test for Gemini Bal Hanuman story generation."""
import json
from story_generator import generate_story

if __name__ == "__main__":
    story = generate_story()
    print(json.dumps(story, ensure_ascii=False, indent=2))
    print("Validated 12-scene Bal Hanuman Ji story generated successfully.")
