
import os
from google import genai

def generate_hindi_story():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set.")
        print("Set your Gemini API key in the terminal and try again.")
        return

    client = genai.Client(api_key=api_key)

    prompt = """
You are an experienced Hindi children's story writer.

Write one original story for children aged 4 to 8 years.

Requirements:
1. Write the story in natural, grammatically correct Hindi.
2. Use Devanagari script only for the Hindi story.
3. Give the story a short, attractive Hindi title.
4. Create exactly 8 numbered scenes.
5. Each scene must contain 2 or 3 complete sentences.
6. Include a child and a friendly animal.
7. Include a small problem and a sensible solution.
8. Give the story a happy and meaningful ending.
9. Use simple words children can understand.
10. Avoid repeated sentences, spelling mistakes and meaningless text.
11. Include a short positive moral.
12. Make the story suitable for approximately 1 to 2 minutes
    of narration.
13. Each scene should be suitable for a separate illustrated
    video scene.

Use this output format:

TITLE: Hindi story title

SCENE 1: Hindi narration
SCENE 2: Hindi narration
SCENE 3: Hindi narration
SCENE 4: Hindi narration
SCENE 5: Hindi narration
SCENE 6: Hindi narration
SCENE 7: Hindi narration
SCENE 8: Hindi narration

MORAL: Hindi moral

Before returning the story, check the Hindi grammar,
spelling, sentence structure and continuity.
Return only the story in the requested format.
"""

    try:
        print("Generating a new Hindi children's story...")

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        story = response.text

        if not story or not story.strip():
            print("ERROR: Gemini returned an empty story.")
            return

        print("\n" + "=" * 50)
        print("GENERATED HINDI CHILDREN'S STORY")
        print("=" * 50)
        print(story)
        print("=" * 50)

        os.makedirs("output", exist_ok=True)

        with open(
            "output/generated_story.txt",
            "w",
            encoding="utf-8"
        ) as file:
            file.write(story)

        print("\nStory saved to: output/generated_story.txt")

    except Exception as error:
        print("\nERROR: Story generation failed.")
        print("Error details:", str(error))


if __name__ == "__main__":
    generate_hindi_story()
