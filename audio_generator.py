
import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
import edge_tts

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

AUDIO_DIR = BASE_DIR / "output" / "audio"

VOICE = os.getenv("TTS_VOICE", "hi-IN-SwaraNeural")


async def create_audio(text, output_path):

    if not text or not text.strip():
        raise ValueError("Narration text is empty.")

    for attempt in range(1, 4):

        try:

            communicate = edge_tts.Communicate(
                text=text,
                voice=VOICE,
                rate="+0%",
                volume="+0%"
            )

            await communicate.save(str(output_path))

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise RuntimeError("Audio file was not created.")

            return str(output_path)

        except Exception as error:

            print(f"Audio attempt {attempt} failed: {error}")

            if attempt == 3:
                raise RuntimeError(
                    f"Could not generate audio: {error}"
                ) from error

            await asyncio.sleep(attempt * 3)


async def generate_all_audio(story):

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    scenes = story.get("scenes", [])

    if len(scenes) != 12:
        raise ValueError("Story must contain exactly 12 scenes.")

    audio_paths = []

    for index, scene in enumerate(scenes, start=1):

        narration = scene.get("narration", "")

        if not narration:
            raise ValueError(
                f"Narration missing in scene {index}"
            )

        audio_path = AUDIO_DIR / f"scene_{index:02d}.mp3"

        print(f"Generating Hindi audio {index}/12...")

        result = await create_audio(
            narration,
            audio_path
        )

        audio_paths.append(result)

    moral = story.get("moral", "")

    if not moral:
        raise ValueError("Story moral is missing.")

    moral_path = AUDIO_DIR / "moral.mp3"

    print("Generating moral narration...")

    moral_result = await create_audio(
        moral,
        moral_path
    )

    audio_paths.append(moral_result)

    print("All 13 audio files generated successfully.")

    return audio_paths


def generate_audio(story):

    return asyncio.run(generate_all_audio(story))
