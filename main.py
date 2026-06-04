from langgraph.graph import StateGraph, END

from agents.summarizer import summarize_meeting
from agents.extractor import extract_action_items
from agents.tracker import track_tasks

from state import State


# ---------------- NODE 1: SUMMARIZER ----------------
def summarizer_node(state: State):
    transcript = state["transcript"]

    summary = summarize_meeting(transcript)

    return {
        "summary": summary
    }


# ---------------- NODE 2: EXTRACTOR ----------------
def extractor_node(state: State):
    transcript = state["transcript"]

    tasks = extract_action_items(transcript)

    return {
        "tasks": tasks
    }


# ---------------- NODE 3: TRACKER ----------------
def tracker_node(state: State):
    tasks = state.get("tasks", [])

    report = track_tasks(tasks)

    return {
        "report": report
    }


# ---------------- BUILD GRAPH ----------------
workflow = StateGraph(State)

workflow.add_node("summarizer", summarizer_node)
workflow.add_node("extractor", extractor_node)
workflow.add_node("tracker", tracker_node)

workflow.set_entry_point("summarizer")

workflow.add_edge("summarizer", "extractor")
workflow.add_edge("extractor", "tracker")
workflow.add_edge("tracker", END)


pipeline = workflow.compile()


# ---------------- RUN TEST ----------------
if __name__ == "__main__":

    sample_transcript = """
    The team discussed the Gemini AI project.

    John will build the API backend.
    Sarah will clean the dataset.
    Mike will prepare documentation.

    Deadline is Friday.
    """
    result = pipeline.invoke({
        "transcript": sample_transcript
    })

    print("\nFINAL OUTPUT:\n")
    print(result["report"])


