from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
import os
from dotenv import load_dotenv
from api.chat_agent import ChatAgent

load_dotenv()
agent = ChatAgent()

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/chat/{chat_id}")
async def chat_endpoint(request: Request, chat_id: str):
    try:
        data = await request.json()
        message = data.get("message")
        history = data.get("history", [])  # optional conversation history

        if not message:
            return JSONResponse(content={"error": "Missing 'message'"}, status_code=400)

        print("DEBUG: message =", chat_id, flush=True)

        result = agent.chat(message, history)

        return {"response": result}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
