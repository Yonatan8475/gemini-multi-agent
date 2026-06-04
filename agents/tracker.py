from datetime import datetime


def track_tasks(tasks):
    """
    Agent 3: Tracks tasks and generates a follow-up report.
    Input: list of task dictionaries
    Output: formatted progress report
    """

    report = []
    report.append("FOLLOW-UP REPORT\n")

    for i, task in enumerate(tasks, start=1):
        task_name = task.get("task", "Unknown task")
        owner = task.get("owner", "Unknown")
        deadline = task.get("deadline", "No deadline")

        report.append(
            f"{i}. {task_name} → {owner} → Due: {deadline} → Status: Pending"
        )

    return "\n".join(report)