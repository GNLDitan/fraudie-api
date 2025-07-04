import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
import os
from dotenv import load_dotenv
from services.chat_agent import ChatAgent
from services.firebase_service import get_chat_history

load_dotenv()
agent = ChatAgent()

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/chat/{chat_id}")
async def chat_endpoint(request: Request, chat_id: str):
    try:
        data = await request.json()
        message = data.get("message")
        history = []  # optional conversation history

        if chat_id:
            history = get_chat_history(chat_id)
        else:
            chat_id = str(uuid.uuid4())
            history = []


        if not message:
            return JSONResponse(content={"error": "Missing 'message'"}, status_code=400)

        result = agent.chat(message, history, chat_id)

        return {"response": result}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
