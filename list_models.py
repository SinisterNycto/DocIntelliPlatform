import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("backend/.env")
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

for m in genai.list_models():
    if 'embedContent' in m.supported_generation_methods:
        print(f"Embedding model: {m.name}")
