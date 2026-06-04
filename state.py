from typing import TypedDict, List, Dict, Any, Optional


class State(TypedDict):
    transcript: str
    summary: Optional[str]
    tasks: List[Dict[str, Any]]
    report: Optional[str]