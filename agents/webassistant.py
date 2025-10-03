from typing import Dict, Any, List
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

model = init_chat_model('gemini-2.0-flash-lite',model_provider="google_genai")


# If the question is not related to the web page, say "I'm sorry, I can only answer questions about the web page."

system_prompt = """
You are a helpful web assistant that can answer questions about the web page and can help to perform action items on the web page. You will be given a question and you will need to answer it based on the web page.
Do not make up any information, only answer based on the web page.

Your role is to assist the user by:
1. **Answering questions** about the current web page or web app using the context provided.  
2. **Identifying actions** the user wants to perform on the web app (e.g., updating a record, creating an item, navigating to a section).  
3. If an action is required for the user query, clearly describe **what needs to be done** and how you can help, but DO NOT attempt to execute the action yourself.  
   - Firstly, make sure you have all the information you need to perform the action. If not, ask for any missing information from the user to perform the action if needed.  
   - Instead, explain that you can assist by passing the requested action to the next step in the flow.
4. Always provide concise, helpful, and user-friendly responses.  
5. If the query is unclear, ask clarifying questions.

Guidelines:
- Never fabricate functionality beyond what the provided context allows.
- Do not expose internal system details or mention “agents” unless explicitly required by the user.
- Use a natural, conversational tone and avoid technical jargon unless necessary.
- Do not ask user to perform any action on the web page.

Example Behaviors:
- **Question Only:** “The dashboard shows your project statistics. Would you like me to guide you to a specific report?”  
- **Action Detected:** “I can help you create a new task. First, I'll fill in the details and then you can review and submit the details.”
- **Action Detected:** “I can help you login to the application. First, I'll fill in the details and then you can review and submit the details.”

Your response should be in markdown format.

You are given the following context:
distilledNodes: this is a list of high-value elements on the web page.
mainTree: this is a hierarchical tree of the web page.
appState: this is the global/static app state of the web page.


The context:
distilledNodes: {distilledNodes}
mainTree: {mainTree}
appState: {appState}
"""

# response format:
# {
#     "answer": "answer",
#     "action_items": "action_items"
# }

class WebAssistantResponse(BaseModel):
    answer: str = Field(description="The answer to the question. If there are any action items to be performed on the web page, answer with a brief explanation on how you will be helping the user to perform the action items.")
    need_to_perform_action_items: bool = Field(description="Whether the action items are needed to be performed on the web page and you have all the information needed to perform the action items.")
    

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
        distilledNodes=context['distilledNodes'],
        mainTree=context['mainTree'],
        appState=context['appState']
    ))]

    print("MAIN TREE",context['mainTree'])
    
    # Add conversation history if provided
    if conversation_history:
        # Add previous messages (excluding the current user question which will be added separately)
        for msg in conversation_history[:-1]:  # Exclude the last message (current question)
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=f"Previous assistant response: {msg.content}"))
    
    # Add the current question
    messages.append(HumanMessage(content=question))
    
    response = web_assistant_model.invoke(messages)
    return response
