from agents.groq_client import generate

def summarize_meeting(transcript: str) -> str:
    """
    Agent 1: Summarizes meeting transcripts into clear bullet points.
    """
    prompt = f"""
    You are an expert meeting assistant.

    Summarize the following meeting transcript into:
    - Key points
    - Decisions made
    - Important context

    Transcript:
    {transcript}
    """
    return generate(prompt)


# Optional test run
if __name__ == "__main__":
    sample = """
    The team discussed the new AI project. John will handle backend APIs.
    Sarah will prepare dataset cleaning. Deadline is Friday.
    """
    print("SUMMARY OUTPUT:\n")
    print(summarize_meeting(sample))