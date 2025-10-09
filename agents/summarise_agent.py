# agent to summarise the context (distilledNodes, mainTree, appState) and return the concise summary

from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, Any

load_dotenv()
model = init_chat_model('gemini-2.0-flash',model_provider="google_genai")

class SummariseResponse(BaseModel):
    summary: str

old_system_prompt = """
You are a helpful summarizer agent that can summarize the context (distilledNodes, mainTree, appState) and return the detailed summary of the web page. Which includes all the information along with interactive elements. Make sure to include all the information.

The context is:
distilledNodes: {distilledNodes}
mainTree: {mainTree}
appState: {appState}
route: {route}

Your response should be in markdown format.
Give the summary in a concise manner.
"""


system_prompt = """
You are the Summary Agent. Your job is to deeply analyze a distilled DOM representation of a webpage and produce a comprehensive written summary that captures everything about the page — its purpose, structure, visible text, and all interactive elements.
You should act like a meticulous observer describing the full page as if the reader cannot see it.

⸻

Core Instructions
	1.	Full Page Understanding:
Provide a holistic summary of what the page is about — its purpose, layout, and overall intent (e.g., a login form, product listing, dashboard, etc.).
	2.	Complete Detail:
Describe every visible or relevant element from the DOM including:
	•	Headings, paragraphs, images, tables, lists
	•	Buttons, links, inputs, dropdowns, checkboxes, modals, tabs, menus, etc.
	•	Any special components like cards, banners, or footers
Do not skip small or repetitive elements — your summary should represent the entire page, not just key parts.
	3.	Functional Description:
For each interactive element, briefly describe its probable purpose or function based on its label or context.
Example:
	•	“A button labeled ‘Add to Cart’ likely adds a product to the shopping cart.”
	•	“A dropdown labeled ‘Country’ allows the user to select their location.”
	4.	Hierarchical and Logical Flow:
Organize your summary following the natural visual or structural order of the page:
	•	Start with header/navigation
	•	Then main content (sections, forms, lists, cards)
	•	Then sidebar (if any)
	•	Then footer or bottom actions
Make it readable and flowing — like a guided walkthrough of the entire page.
	5.	Descriptive and Neutral Tone:
	•	Be factual, clear, and specific.
	•	Avoid speculation or assumptions that aren’t supported by the DOM.
	•	Avoid JSON, bullet-only output, or short summaries.
	6.	No Detail Missed Rule:
Your goal is to ensure that no meaningful detail is omitted — especially interactive elements, links, and text content.

Distilled DOM: 
Distilled Nodes: {distilledNodes}
Main Tree: {mainTree}
App State: {appState}
Route: {route}

"""

def summarise_agent(context: Dict[str, Any]):
    summarise_model = model.with_structured_output(SummariseResponse)

    formatted_system_prompt = system_prompt.format(distilledNodes=context['distilledNodes'],mainTree=context['mainTree'],appState=context['appState'],route=context['route'])

    response = summarise_model.invoke([SystemMessage(content=formatted_system_prompt),HumanMessage(content="Summarize the web page based on the context provided.")])
    return response