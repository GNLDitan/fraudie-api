# api/me_agent.py

from pathlib import Path
import uuid
from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader

from helper.load_tool_schema import load_tool_schema, load_template
from services.database_agent import ask
from services.firebase_service import save_chat_history

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_PATH = BASE_DIR / "config" / "prompt" / "summary.txt"

record_user_schema = load_tool_schema("record_user_details.json")
record_unknown_schema = load_tool_schema("record_unknown_question.json")
query_question_schema = load_tool_schema("query_question_database.json")

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

def query_question_database(question):
    response = ask(question)
    return response


tools = [
    {"type": "function", "function": query_question_schema},
    {"type": "function", "function": record_user_schema},
    {"type": "function", "function": record_unknown_schema}
]

class ChatAgent:
    def __init__(self):
        print("DEBUG: message =", os.getenv("OPENAI_API_KEY"), flush=True)

        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.name = load_template("owner_name.txt")
        with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
            self.summary = f.read()
        
        self.system_prompt_template = load_template("persona.txt")

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)

            # Use if-else instead of globals()
            if tool_name == "record_user_details":
                result = record_user_details(**arguments)
            elif tool_name == "record_unknown_question":
                result = record_unknown_question(**arguments)
            elif tool_name == "query_question_database":
                result = query_question_database(**arguments)
            else:
                result = {"error": f"No handler for tool '{tool_name}'"}

            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results

    def system_prompt(self):
      return self.system_prompt_template.format(
            name=self.name,
            summary=self.summary
        )

    def chat(self, message, history=[], chat_id=None):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools
            )
            if response.choices[0].finish_reason == "tool_calls":
                print("DEBUG: tool_calls =", response.choices[0].finish_reason , flush=True)
                tool_calls = response.choices[0].message.tool_calls
                messages.append(response.choices[0].message)
                messages.extend(self.handle_tool_call(tool_calls))
            else:
                done = True

        assistant_reply = response.choices[0].message.content
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": assistant_reply})
        save_chat_history(chat_id, history)
        return response.choices[0].message.content
