from typing import Dict, Any, List
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from contexts.app_context import web_app_context

load_dotenv()

model = init_chat_model('gemini-2.0-flash',model_provider="google_genai")


# If the question is not related to the web page, say "I'm sorry, I can only answer questions about the web page."

system_prompt = """
You are a helpful web assistant that can answer questions about the web page and can help to perform action items on the web page. You will be given a question and you will need to answer it based on the web page.
Do not make up any information, only answer based on the web page.

Your role is to assist the user by:
1. **Answering questions** about the current web page or web app using the context provided.  
2. **Identifying actions** the user wants to perform on the web app (e.g., updating a record, creating an item, navigating to a section).  
3. If an action is required for the user query, first check if you have all the necessary information to perform the action. If you do, clearly describe **what needs to be done** and how you can help, but DO NOT attempt to execute the action yourself.  
   - If you do not have all the necessary information to perform the action, ask the user for it before proceeding.  
   - If you have all the required information, explain that you can assist by passing the requested action to the next step in the flow.
4. Always provide concise, helpful, and user-friendly responses.  
5. If the query is unclear, ask clarifying questions.

Guidelines:
- Never fabricate functionality beyond what the provided context allows.
- Do not expose internal system details or mention “agents” unless explicitly required by the user.
- Use a natural, conversational tone and avoid technical jargon unless necessary.
- Do not ask user to perform any action on the web page.
- Do not assume any information. If you don't have the information, ask the user for it.
- If you have all the information then no need to check for confirmation from the user.

Example Behaviors:
- **Question Only:** answer: “The dashboard shows your project statistics. Would you like me to guide you to a specific report?” & need_to_perform_action_items: false
- **Action Detected and Action Information Missing:** answer: “To create a new task, I need the following information: title, description, due date, and assignee.” & need_to_perform_action_items: false
- **Action Detected and Action Information Provided:** answer: “I can help you create a new task. First, I'll fill in the details and then you can review and submit the details.” & need_to_perform_action_items: true

Your response should be in markdown format.

You are given the following context:
web page summary: {web_page_summary}
conversation history: {conversation_history}
web app context: {web_app_context}

NOTE: **If you do not have the required information to perform the action items, ask the user for it & need_to_perform_action_items should be false.**

"""

# response format:
# {
#     "answer": "answer",
#     "action_items": "action_items"
# }

class WebAssistantResponse(BaseModel):
    answer: str = Field(description="The answer to the question. If there are any action items to be performed on the web page, answer with a brief explanation on how you will be helping the user to perform the action items.")
    need_to_perform_action_items: bool = Field(description="Whether the action items (fill input field, navigate, click button, etc.) are needed to be performed on the web page or need to navigate to another page and you have all the information needed to perform the action items. Eg: User asks to create a new task, you have all the information needed to create a new task, so set this to true.")
    

def web_assistant_agent(context: Dict[str, Any], question: str, conversation_history: List = None):
    """
    This function is used to answer a question based on the context of the web page.
    It uses the gemini-2.0-flash-lite model to answer the question.
    It uses the context to answer the question.
    It returns the answer in markdown format.
    It uses the distilledNodes, mainTree, and appState to answer the question.
    It uses the question to answer the question.
    It can use conversation history for context-aware responses.
    """

    web_assistant_model = model.with_structured_output(WebAssistantResponse)

    # Build messages list with system prompt and conversation history
    messages = [SystemMessage(content=system_prompt.format(
        web_page_summary=context,
        conversation_history=conversation_history,
        web_app_context=web_app_context
    ))]

    
    # Add conversation history if provided
    # if conversation_history:
    #     # Add previous messages (excluding the current user question which will be added separately)
    #     for msg in conversation_history[:-1]:  # Exclude the last message (current question)
    #         if msg.role == "user":
    #             messages.append(HumanMessage(content=msg.content))
    #         elif msg.role == "assistant":
    #             messages.append(AIMessage(content=f"Previous assistant response: {msg.content}"))
    
    # Add the current question
    messages.append(HumanMessage(content=question))

    # beautfully print all the messages in the messages list but exclude the first system message
    for msg in messages[1:]:
        print(msg.content)
    
    response = web_assistant_model.invoke(messages)
    return response
