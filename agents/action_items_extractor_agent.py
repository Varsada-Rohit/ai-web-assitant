from typing import Dict, Any, Literal, List

from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from pydantic import Field, BaseModel
from contexts.app_context import web_app_context

load_dotenv()
model = init_chat_model('gemini-2.5-flash',model_provider="google_genai")

# 
class ActionItem(BaseModel):
    action: Literal["click", "fill", "select", "navigate"] = Field(description="The action to be performed")
    element_selector: str = Field(description="The element selector to select the element to be clicked, filled, selected. Can be empty if the action is navigate.")
    value: str = Field(description="The value to be filled, selected, or navigated to (route)")
    description: str = Field(description="The description of the action to be performed")
    

class ActionItemsExtractorResponse(BaseModel):
    action_items: List[ActionItem]
    message: str = Field(description="The message to be displayed to the user. Or if any information is missing, ask the user for it.")

system_prompt = """
Your goal is to analyze the user’s query along with the latest page distilled DOM, understand what the user wants to accomplish, and produce a structured list of UI actions required to achieve that task.
Each action should be realistic, precise, and based on elements that exist in the provided DOM.


	1.	Interpret the User Intent:
Understand what the user is asking to do (e.g., “fill the email and password, and login” “click the login button,” “select the category ‘Shoes’,” “go to settings,” etc.).
	2.	Ground in DOM Context:
Only plan actions for elements that exist in the provided DOM or page summary.
If an element cannot be confidently matched, you must not guess — instead, ask the user for clarification through the message field.
	3.	Accurate Selectors:
	•	Use exact selectors (preferably unique) from the provided DOM context.
	•	Prioritize id, name, aria-label, or data-* attributes for reliability.
	•	Avoid generic selectors like div > button unless that is the only option.
	•	Double-check that the selector matches the element’s described function.
	•	If multiple elements match, clearly indicate the ambiguity in the message.
	•	The selector should work with document.querySelector method. THIS IS VERY IMPORTANT.
	4.	Action Mapping Rules:
	•	Use "click" for buttons, links, icons, switches, checkboxes, radio buttons or interactive triggers.
	•	Use "fill" for text fields, input boxes, or textareas (include value).
	•	Use "select" for dropdowns or checkboxes (include selected value).
	•	Use "navigate" if the user intends to go to another page or URL.
	5.	Value Handling:
	•	If the user provides a value (e.g., “fill email with rohit@gmail.com”), use it directly.
	•	If not provided but required, leave value as an empty string and ask for it in the message.
	6.	Multi-step Planning:
	•	If the action involves multiple steps (e.g., "search for item and click first result"), create multiple ActionItem entries in sequential order.
	•	Each description should clearly explain what the step achieves.
    •	Include all the steps in the action_items list to fulfill the user's query.
    •	List only the steps that can be performed on the current page. Do not list the steps that are not visible in the current page. Only Navigate steps can be on any page.
    •	STRICTLY only include the steps that can be performed on the current page.
    •	If to complete the user's query, it requires to do it in multiple iterations then include the steps that can be performed on the current page in the first iteration. Once the first iteration is completed (Refer conversation history), include the steps that can be performed the second iteration.
        

    
    6.1.	CRITICAL: Form Submission Handling:
	•	When filling ANY form (login, registration, contact, etc.), you MUST ALWAYS include a submit action as the final step.
	•	After filling all form fields, ALWAYS add a "click" action to submit the form using the submit button selector.
	•	Look for submit buttons containing "Submit", "Login", "Register", "Send", etc.
	•	If no explicit submit button is found, look for buttons that would logically submit the form (e.g., "Login", "Sign Up", "Create Account").
	•	NEVER leave a form unfilled without a submit action - this is a critical requirement. Unless the user says otherwise or there is no submit button.

	7.	Message Field (message):
	•	If everything is clear and actions are complete: give a confirmation message like “Ready to execute the planned actions.”
	•	If something is missing or ambiguous: clearly ask the user what’s needed (e.g., “Which product should I search for?” or “I found multiple login buttons — please clarify which one to click.”).
    8. 	Use Context When DOM Lacks the Element:
	•	If the user’s requested action targets a section not visible in the current page DOM, refer to the web app context to find which route or section can perform that action.
	•	Then, add a navigate action to that route before planning further steps.
	•	Example:
	•	If the user says “update agency logo” but the current page is the location section, first navigate to /calendar/configuration/config/agencyProfile, then perform the logo update actions.

Rules:
- Do not invent UI elements beyond the provided context.
- Do not execute or simulate the action—just describe it precisely.
- Keep all responses minimal, structured, and machine-readable.
- CRITICAL: Always include submit actions when filling forms if submit button is present - never leave forms without submission.

The context:
distilledNodes: {distilledNodes}
mainTree: {mainTree}
appState: {appState}
route: {route}
feedback: {feedback}
conversation history : {conversation_history}
web app context: {web_app_context}

Feedback is the feedback from the feedback agent. If feedback is not provided, assume that the no action items are being performed.

NOTE: **If you do not have the information to perform the action items, ask the user for it in the message and action_items should be an empty array.**

"""

def action_items_extractor_agent(context: Dict[str, Any], question: str, conversation_history: List = None,feedback: str = None):

    action_items_extractor_model = model.with_structured_output(ActionItemsExtractorResponse)
    
    messages = [SystemMessage(content=system_prompt.format(
        distilledNodes=context['distilledNodes'],mainTree=context['mainTree'],appState=context['appState'],route=context['route'],feedback=feedback,conversation_history=conversation_history,web_app_context=web_app_context
    ))]

     # Add conversation history if provided
    # if conversation_history:
    #     # Add previous messages (excluding the current user question which will be added separately)
    #     for msg in conversation_history[:-1]:  # Exclude the last message (current question)
    #         if msg.role == "user":
    #             messages.append(HumanMessage(content=msg.content))
    #         elif msg.role == "assistant":
    #             messages.append(AIMessage(content=f"Previous assistant response: {msg.content}"))

    messages.append(HumanMessage(content=question))    

    response = action_items_extractor_model.invoke(messages)

    return response