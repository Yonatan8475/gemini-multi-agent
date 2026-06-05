# agents/transcriber.py
# Save this as: agents/transcriber.py

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def transcribe_audio(audio_bytes: bytes, language: str = "en") -> dict:
    """
    Agent 0 — Transcriber
    Converts audio to text using Groq Whisper large-v3.

    Supports:
    - English  (language="en")
    - Amharic  (language="am")
    - Auto     (language="auto")

    Returns:
        {
            "transcript": "the full transcribed text",
            "language":   "en" or "am",
            "duration":   12.5   (seconds)
        }
    """
    try:
        transcription = client.audio.transcriptions.create(
            file=("recording.webm", audio_bytes),
            model="whisper-large-v3",
            language=language if language != "auto" else None,
            response_format="verbose_json",
        )

        return {
            "transcript": transcription.text,
            "language": getattr(transcription, "language", language),
            "duration": getattr(transcription, "duration", 0.0),
        }

    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")


# ── TEST ──────────────────────────────────────
if __name__ == "__main__":
    print("Transcriber Agent 0 — Ready")
    print("Languages: English (en), Amharic (am), Auto-detect (auto)")
    print("Model: Groq Whisper Large V3")