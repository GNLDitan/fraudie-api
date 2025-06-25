import json
import openai
from helper.load_tool_schema import load_template
import pyodbc
import os
from dotenv import load_dotenv

from services.firebase_service import BASE_DIR

load_dotenv()

# Load connection info
SQL_DRIVER = os.getenv("SQL_DRIVER")
SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

# Setup OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

CONFIG_PATH = BASE_DIR / "config"
SCHEMA_PATH = CONFIG_PATH / "database" / "schema" / "dbschema.txt"
SQL_EXPERT_PATH = CONFIG_PATH / "prompt" / "sql_expert.txt"

# Connection setup
def get_connection():
    conn_str = (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASSWORD}"
    )
    return pyodbc.connect(conn_str)


# Ask LLM to convert user question to SQL
def generate_sql_from_question(question: str) -> str:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as s:
        schema = s.read()
    with open(SQL_EXPERT_PATH, "r", encoding="utf-8") as s:
        sql_expert = s.read()


    print("DEBUG: modified_prompt =", sql_expert, flush=True)
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": sql_expert},
            {"role": "user", "content":  f"Schema:\n{schema}" },
            {"role": "user", "content": f"Convert to SQL: {question}"}
        ]
    )
    sql = response.choices[0].message.content.strip()
    return sql


# Execute SQL and return results
def execute_sql(query: str):
    try:
        conn = get_connection()
        if not conn:
           print("ERROR: Unexpected error:", conn, flush=True)

        cursor = conn.cursor()
        cursor.execute(query)

        print("DEBUG: cursor.execute =", cursor, flush=True)

        if not cursor.description:
            return []  # No data returned

        columns = [column[0] for column in cursor.description]
        print("DEBUG: cursor.columns =", columns, flush=True)

        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print("DEBUG: cursor.results =", results, flush=True)

        return results

    except pyodbc.Error as e:
        print("ERROR: pyodbc error:", e, flush=True)

    except Exception as e:
        print("ERROR: Unexpected error:", e, flush=True)

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

def format_readable_answer(question: str, result: list[dict]):
    prompt = load_template("query_assistant.txt")
    prompt = prompt.format(question=question, data_text=result) 
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a data summarizer."},
            {"role": "user", "content": prompt}
        ]
    )
    print("DEBUG: completion =", completion.choices[0].message.content, flush=True)
    return completion.choices[0].message.content

# Combined: question -> SQL -> result
def ask(question: str):
    print("DEBUG: sql =", question, flush=True)
    # Call Ai Convert question to SQL
    sql = generate_sql_from_question(question)
    print("DEBUG: sql =", sql, flush=True)
    # Execute SQL
    executed = execute_sql(sql)
    print("DEBUG: executed =", executed, flush=True)
    # Call Ai to make it readable
    final_answer = format_readable_answer(question, executed)
    return final_answer