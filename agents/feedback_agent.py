from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import List

from agents.action_items_extractor_agent import ActionItem
load_dotenv()


model = init_chat_model('gemini-2.0-flash',model_provider="google_genai")


class FeedbackResponse(BaseModel):
    isCompleted: bool = Field(description="Whether the user's request has been successfully fulfilled based on the changes in the DOM and the initial page summary.")
    message: str = Field(description="The message to be displayed to the user. whether the user query is being served by the action items or not with the reason.")
    should_wait: bool = Field(description="Whether the user should wait for more DOM updates.")

system_prompt = """
You are a feedback evaluation agent that verifies whether the user’s requested task has been successfully completed on the web page.

Inputs you receive:
	1.	User Query: The original question or command from the user (e.g., “Add item to cart”, “Open settings page”, “Show all employees”).
	2.	Page Summary (Before Actions): A textual summary of the page before any actions were performed.
	3.	Distilled Dom (After Actions): A distilled DOM of the page after all actions were performed. It contains distilledNodes, mainTree, appState and route.
    4.  Action Items: The action items that were performed on the page.

Your Goal:
You analyze the initial page summary and the DOM state after actions to decide if:
	1.	The user’s goal is completed,
	2.	The goal is not yet completed, or
	3.	The page is still loading and you should wait for more DOM updates.

Instructions:
	1.	Compare the page summary before and DOM after actions.
	2.	Analyze whether the DOM reflects the expected outcome described in the user query and the action items (Mainly validate the action items are performed on the web page successfully).
	3.	If the action visibly or logically satisfies the intent and no more action items are needed to complete the user query, mark it as completed.
	4.	If not, mark it as incomplete and explain what is done and  what is missing or incorrect.
	5.  Format the message with proper explanation and reasoning.
	6.  In conversation history, action items are generated and expected to be performed on the web page. So check if the action items are performed on the web page successfully. Do no assume that the action items are performed on the web page successfully. And if you have information for action items then no need to confirm from the user or ask for it again instead just say what is the next step.


User Query: {user_query}
Page Summary (Before Actions): {page_summary}
Distilled Dom (After Actions): {distilled_dom}
conversation history : {conversation_history}

"""

def feedback_agent(action_items: List[ActionItem], user_query: str, page_summary: str, distilled_dom: str, conversation_history: str):
    print(f"\n🔄 FEEDBACK AGENT STARTED")
    print(f"   User Query: {user_query[:100]}...")
    print(f"   Action Items Count: {len(action_items)}")
    print(f"   Page Summary Length: {len(page_summary)} chars")
    print(f"   Distilled DOM Length: {len(str(distilled_dom))} chars")
    
    feedback_model = model.with_structured_output(FeedbackResponse)

    formatted_system_prompt = system_prompt.format(action_items=action_items, user_query=user_query, page_summary=page_summary, distilled_dom=distilled_dom, conversation_history=conversation_history)
	
    print('🤖 TRIGGERED FEEDBACK AGENT - Calling AI model...')

    response = feedback_model.invoke([SystemMessage(content=formatted_system_prompt),HumanMessage(content="Validate the action items and return the message to be displayed to the user.")])
    
    print(f"✅ FEEDBACK AGENT COMPLETED")
    print(f"   Completed: {response.isCompleted}")
    print(f"   Should Wait: {response.should_wait}")
    print(f"   Message Length: {len(response.message)} chars")
    
    return response