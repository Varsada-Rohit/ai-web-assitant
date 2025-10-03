from dotenv import load_dotenv
import os
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage
from langchain_core.messages import HumanMessage

load_dotenv()

# System prompt
system_prompt = """
You are a helpful assistant that can answer questions about the document. You will be given a question and you will need to answer it based on the document.
Do not make up any information, only answer based on the document.
Your response should be in markdown format.
If the question is not related to the document, say "I'm sorry, I can only answer questions about the document."

If the question is general, respond politely to the question. ask for more details if needed or ask how you can help.

The document is:
{document}

"""

def Answer_Generator(query: str, document: str):
    model = init_chat_model('gemini-1.5-flash',model_provider="google_genai")
    response = model.invoke([SystemMessage(content=system_prompt.format(document=document)),HumanMessage(content=query)])
    return response.text()