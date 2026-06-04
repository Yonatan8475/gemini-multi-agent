from agents.groq_client import generate
import json

def extract_action_items(transcript: str):
    """
    Agent 2: Extract structured action items from meeting text.
    Returns JSON list of tasks.
    """
    prompt = f"""
    You are an expert project manager.

    Extract ALL action items from the meeting transcript below.

    Return ONLY valid JSON in this format:
    [
      {{
        "task": "string",
        "owner": "string",
        "deadline": "string or null"
      }}
    ]

    Rules:
    - Do NOT add explanations
    - Do NOT wrap in markdown code blocks
    - If owner is unknown, use "Unknown"
    - If deadline is missing, use null

    Transcript:
    {transcript}
    """

    response_text = generate(prompt)

    # Clean any markdown formatting Groq might add
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    try:
        return json.loads(clean)
    except:
        return response_text


# Optional test run
if __name__ == "__main__":
    sample_text = """
    John will build the API backend. Sarah will clean the dataset.
    Mike will prepare documentation. Deadline is Friday.
    """
    result = extract_action_items(sample_text)
    print("\nEXTRACTED ACTION ITEMS:\n")
    print(result)