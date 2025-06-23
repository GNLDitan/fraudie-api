# api/me_agent.py

from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader

from helper.load_tool_schema import load_tool_schema, load_template

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "me" / "linkedin.pdf"
SUMMARY_PATH = BASE_DIR / "me" / "summary.txt"

record_user_schema = load_tool_schema("record_user_details.json")
record_unknown_schema = load_tool_schema("record_unknown_question.json")

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


tools = [{"type": "function", "function": record_user_schema},
         {"type": "function", "function": record_unknown_schema}]

class ChatAgent:
    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.name = load_template("owner_name.txt")
        reader = PdfReader(str(PDF_PATH))
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("config/prompt/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

        self.system_prompt_template = load_template("persona.txt")

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results

    def system_prompt(self):
      return self.system_prompt_template.format(
            name=self.name,
            summary=self.summary,
            linkedin=self.linkedin
        )

    def chat(self, message, history=[]):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools
            )
            if response.choices[0].finish_reason == "tool_calls":
                tool_calls = response.choices[0].message.tool_calls
                messages.append(response.choices[0].message)
                messages.extend(self.handle_tool_call(tool_calls))
            else:
                done = True
        return response.choices[0].message.content
