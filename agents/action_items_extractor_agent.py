from typing import Dict, Any, Literal, List

from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from pydantic import Field, BaseModel

load_dotenv()
model = init_chat_model('gemini-2.0-flash-lite',model_provider="google_genai")

# 
class ActionItem(BaseModel):
    action: Literal["click", "fill", "select", "navigate"] = Field(description="The action to be performed")
    element_selector: str = Field(description="The element selector to select the element to be clicked, filled, selected, or navigated to")
    value: str = Field(description="The value to be filled, selected, or navigated to")
    description: str = Field(description="The description of the action to be performed")
    

class ActionItemsExtractorResponse(BaseModel):
    action_items: List[ActionItem]

system_prompt = """
Your role is to EXTRACT all actionable steps from the user’s request using the context provided to be performed on the web page.

Your job:
1. Identify all the actions that are needed to be performed on the web page to fulfill the request.
2. Classify each action strictly as one of these types: ["click", "fill", "select", "navigate"].
   - click → clicking a button, link, checkbox, etc.
   - fill → entering text/input into a field.
   - select → choosing an option from a dropdown, radio group, or multi-select.
   - navigate → moving to a different page, tab, or section.
3. Ensure the element selector is accurate by cross-referencing with the provided context to avoid failures.
4. Preserve the natural sequence of steps if multiple actions are required.
5. If no action is needed, return an empty array.

Rules:
- Do not invent UI elements beyond the provided context.
- Do not execute or simulate the action—just describe it precisely.
- Keep all responses minimal, structured, and machine-readable.

The context:
distilledNodes: {distilledNodes}
mainTree: {mainTree}
appState: {appState}

"""

def action_items_extractor_agent(context: Dict[str, Any], question: str):

    action_items_extractor_model = model.with_structured_output(ActionItemsExtractorResponse)

    response = action_items_extractor_model.invoke([SystemMessage(content=system_prompt.format(distilledNodes=context['distilledNodes'],mainTree=context['mainTree'],appState=context['appState'])),HumanMessage(content=question)])

    return response