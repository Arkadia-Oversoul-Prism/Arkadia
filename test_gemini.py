import os
import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")
print("KEY PRESENT:", bool(api_key))

genai.configure(api_key=api_key)

for name in ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]:
    print("Trying:", name)
    try:
        model = genai.GenerativeModel(name)
        resp = model.generate_content("Say: Arkadia is online.")
        print("OK:", name, "→", resp.text[:80])
    except Exception as e:
        print("ERROR:", name, "→", type(e).__name__, e)
