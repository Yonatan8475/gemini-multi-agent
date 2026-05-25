from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("AIzaSyCvy9NzNRhXt4RJ3ZpUc-prgK99F4pUQ-A"))

response = client.models.generate_content(
    model="models/gemini-flash-latest",
    contents="Say hello and confirm you are Gemini in one sentence."
)

print(response.text)