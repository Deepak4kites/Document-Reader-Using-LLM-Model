from typing import TypedDict
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    messages: list
    filePath: str
    fileName: str
    result: dict
    pdfText: str
    json_data: dict
    image: bool

graph = StateGraph(AgentState)
state = AgentState()