import asyncio
import edge_tts

async def main():
    text = "नमस्ते बच्चों, आज हम एक नई कहानी सुनेंगे।"
    voice = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await voice.save("output/voice_test.mp3")
    print("Hindi voice test successful")

asyncio.run(main())
