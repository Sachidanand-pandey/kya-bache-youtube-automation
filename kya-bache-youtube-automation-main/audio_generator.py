import asyncio
from pathlib import Path
import edge_tts

VOICE = "hi-IN-SwaraNeural"
AUDIO_DIR = Path("output/audio")

async def create_one_audio(text, path):
    communicator = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="-3%",
        volume="+0%"
    )
    await communicator.save(str(path))

async def create_narrations(story):
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, scene in enumerate(story["scenes"], start=1):
        path = AUDIO_DIR / f"scene_{index:02d}.mp3"
        print(f"Creating Hindi narration {index}/{len(story['scenes'])}")
        await create_one_audio(scene, path)
        paths.append(path)

    moral_path = AUDIO_DIR / "moral.mp3"
    await create_one_audio(story["moral"], moral_path)
    paths.append(moral_path)
    return paths

def generate_audio(story):
    return asyncio.run(create_narrations(story))
