import os
import time
import google.generativeai as genai
from suno import Suno, ModelVersions
from dotenv import load_dotenv

# 1. Load the secret keys from the .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SUNO_COOKIE = os.getenv("SUNO_COOKIE")

genai.configure(api_key=GOOGLE_API_KEY)

def run_pandabrief():
    print("\n🐼 --- PANDA BRIEF STUDIO ---")
    topic = input("1. What topic do you want news on? (e.g. 'Crypto', 'AI'): ")
    genre = input("2. What music genre? (e.g. 'Drill Rap', 'Country'): ")

    # --- RESEARCH ---
    print(f"\n🕵️  Researching '{topic}'...")
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    search_results = model.generate_content(
        f"Find 3 breaking news facts from today about: {topic}.",
        tools='google_search_retrieval'
    )

    # --- WRITE LYRICS ---
    print("✍️  Writing lyrics...")
    lyrics_response = model.generate_content(f"""
    Write a song about this news.
    NEWS: {search_results.text}
    GENRE: {genre}
    RULES: [Verse 1], [Chorus], [Verse 2]. Make it catchy.
    OUTPUT ONLY THE LYRICS.
    """)
    lyrics = lyrics_response.text

    # --- COMPOSE ---
    print("🎧 Sending to Suno...")
    client = Suno(cookie=SUNO_COOKIE, model_version=ModelVersions.CHIRP_V3_5)
    songs = client.generate(
        prompt=lyrics,
        tags=genre,
        is_custom=True,
        wait_audio=True
    )

    print("\n✅ DONE! Here are your songs:")
    for s in songs:
        print(f"🔗 {s.audio_url}")

if __name__ == "__main__":
    run_pandabrief()
