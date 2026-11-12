import json
import os
import random
import re
from pathlib import Path

OUTPUT_DIR = Path("output")
STORY_FILE = OUTPUT_DIR / "story.json"

FALLBACK_STORIES = [
    {
        "title": "जादुई जंगल का रहस्यमयी दरवाज़ा",
        "character": "चीकू खरगोश",
        "scenes": [
            "हरे-भरे सुंदर जंगल में चीकू नाम का एक छोटा खरगोश रहता था। उसे नई जगहें खोजने का बहुत शौक था।",
            "एक सुबह चीकू को बड़े पेड़ों के पीछे सुनहरी रोशनी दिखाई दी। वह धीरे-धीरे उस रोशनी की ओर बढ़ा।",
            "वहाँ एक पुराना सुनहरा दरवाज़ा था। दरवाज़े पर लिखा था, जो दूसरों की मदद करता है वही इसे खोल सकता है।",
            "तभी चीकू को पास से किसी के रोने की आवाज़ सुनाई दी। एक नन्हा हिरन काँटों में फँसा हुआ था।",
            "चीकू ने डरने के बजाय ध्यान से काँटे हटाए। उसने हिरन को चोट पहुँचाए बिना बाहर निकाल लिया।",
            "हिरन ने चीकू को धन्यवाद दिया और बताया कि जंगल का झरना सूख रहा है। सभी जानवर पानी के लिए परेशान थे।",
            "चीकू और हिरन झरने तक पहुँचे। वहाँ गिरे हुए पेड़ों और पत्थरों ने पानी का रास्ता रोक दिया था।",
            "दोनों ने मिलकर छोटे पत्थर हटाए। फिर बंदर, हाथी और चिड़ियों ने भी उनकी मदद की।",
            "हाथी ने अपनी सूँड़ से भारी लकड़ी हटाई और बंदरों ने सूखी टहनियाँ साफ कीं। थोड़ी देर में पानी फिर बहने लगा।",
            "जंगल में खुशी लौट आई। प्यासे जानवरों ने साफ पानी पिया और सबने मिलकर झरने के आसपास सफाई रखी।",
            "तभी सुनहरा दरवाज़ा अपने आप खुल गया। उसके पीछे कोई खजाना नहीं, बल्कि रंग-बिरंगे फूलों से भरा सुंदर बगीचा था।",
            "चीकू समझ गया कि असली जादू मिल-जुलकर अच्छे काम करने में है। उस दिन से जंगल के सभी जानवर एक-दूसरे की मदद करने लगे।"
        ],
        "moral": "सीख: मिल-जुलकर दूसरों की मदद करने से बड़ी से बड़ी मुश्किल आसान हो जाती है।"
    },
    {
        "title": "नन्हे हाथी की बड़ी हिम्मत",
        "character": "मोटू हाथी",
        "scenes": [
            "सुंदर वन में मोटू नाम का एक नन्हा हाथी रहता था। वह बहुत दयालु था, लेकिन अपनी ताकत को लेकर हमेशा संकोच करता था।",
            "एक दिन तेज़ हवा चली और जंगल के छोटे पुल पर एक बड़ा पेड़ गिर गया। दूसरी ओर कई जानवर अपने घरों तक नहीं पहुँच पा रहे थे।",
            "बंदर ने पेड़ हटाने की कोशिश की, लेकिन वह बहुत भारी था। सभी परेशान होकर उपाय सोचने लगे।",
            "मोटू ने धीरे से कहा कि वह मदद करना चाहता है। कुछ जानवरों ने सोचा कि वह अभी बहुत छोटा है।",
            "मोटू ने हार नहीं मानी। उसने पहले अपनी सूँड़ से छोटी डालियाँ हटाईं और रास्ता साफ किया।",
            "फिर उसने अपने दोस्तों को सुरक्षित दूरी पर खड़े होने को कहा। सबने मिलकर पेड़ को सही दिशा में धकेलने की योजना बनाई।",
            "मोटू ने अपनी सूँड़ और मजबूत पैरों से पेड़ को धीरे-धीरे सरकाया। दोस्तों ने छोटी टहनियाँ हटाईं।",
            "कुछ कोशिशों के बाद पेड़ रास्ते से हट गया। पुल फिर से सभी के लिए खुल गया।",
            "दूसरी ओर फँसे जानवर खुशी से लौट आए। उन्होंने मोटू को धन्यवाद दिया।",
            "मोटू मुस्कुराया और बोला कि अकेले वह यह काम नहीं कर पाता। सबकी मदद से ही रास्ता खुला।",
            "उस दिन जंगल में सबने मिलकर पुल के पास सुरक्षा के लिए मजबूत लकड़ियाँ लगाईं।",
            "मोटू को समझ आया कि हिम्मत का मतलब डर न होना नहीं, बल्कि सही काम के लिए कोशिश करना है।"
        ],
        "moral": "सीख: आत्मविश्वास और मिल-जुलकर काम करने से हम कठिन काम भी कर सकते हैं।"
    }
]

def clean_json_text(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text

def validate_story(data):
    if not isinstance(data, dict):
        raise ValueError("Story response is not a JSON object.")
    for key in ("title", "character", "scenes", "moral"):
        if key not in data:
            raise ValueError(f"Missing story field: {key}")
    if not isinstance(data["scenes"], list) or len(data["scenes"]) < 10:
        raise ValueError("Story must contain at least 10 scenes.")
    data["scenes"] = [str(scene).strip() for scene in data["scenes"] if str(scene).strip()]
    if len(data["scenes"]) < 10:
        raise ValueError("Not enough valid scenes.")
    data["title"] = str(data["title"]).strip()
    data["character"] = str(data["character"]).strip()
    data["moral"] = str(data["moral"]).strip()
    return data

def generate_with_gemini():
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)
    prompt = """
Write a completely original Hindi moral story for children aged 4–9.
Return ONLY valid JSON with keys: title, character, scenes, moral.
Use Devanagari Hindi. Create exactly 12 scenes. Each scene should have
2–3 natural, connected sentences suitable for voice narration.
The story must have a strong opening, a small problem, a safe and logical
solution, a happy ending, and a positive moral. Avoid violence, frightening
content, copyrighted characters, brand names, and repeated plots.
Make the total narration suitable for approximately 3–5 minutes.
JSON example structure:
{"title":"...", "character":"...", "scenes":["..."], "moral":"..."}
"""
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt
    )
    if not getattr(response, "text", None):
        raise RuntimeError("Gemini returned an empty response.")
    return validate_story(json.loads(clean_json_text(response.text)))

def generate_story():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        story = generate_with_gemini()
        story["source"] = "gemini"
        print("Story generated using Gemini.")
    except Exception as exc:
        print(f"Gemini unavailable; using offline fallback story. Reason: {exc}")
        story = validate_story(random.choice(FALLBACK_STORIES).copy())
        story["source"] = "offline_fallback"

    STORY_FILE.write_text(
        json.dumps(story, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return story

if __name__ == "__main__":
    print(json.dumps(generate_story(), ensure_ascii=False, indent=2))
