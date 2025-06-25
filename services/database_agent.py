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
PROMPT_PATH = CONFIG_PATH / "prompt"

SCHEMA_PATH = CONFIG_PATH / "database" / "schema" / "dbschema.txt"
SQL_EXPERT_PATH = PROMPT_PATH / "sql_expert.txt"
STRICT_CLASSIFIER_PATH = PROMPT_PATH / "strict_classifier.txt"

SQL_EXPERT_PATHS = {
    "user": PROMPT_PATH / "db/sql_user_expert.txt",
    "member": PROMPT_PATH /"db/sql_member_expert.txt",
    "transaction": PROMPT_PATH / "db/sql_transaction_expert.txt",
    "group": PROMPT_PATH / "db/sql_group_expert.txt",
    "unknown": PROMPT_PATH / "db/sql_fallback_expert.txt"
}


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
def generate_sql_from_question(question: str, domain: str) -> str:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as s:
        schema = s.read()
        
    prompt_path = SQL_EXPERT_PATHS.get(domain, SQL_EXPERT_PATHS["unknown"])
    with open(prompt_path, "r", encoding="utf-8") as f:
        sql_prompt = f.read()

    print("DEBUG: using prompt for domain:", domain, flush=True)
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": sql_prompt},
            {"role": "user", "content": f"Schema:\n{schema}"},
            {"role": "user", "content": f"Convert to SQL: {question}"}
        ]
    )
    sql = response.choices[0].message.content.strip()
    return sql


def classify_question_domain(question: str) -> str:
    try:
        with open(STRICT_CLASSIFIER_PATH, "r", encoding="utf-8") as s:
            strict_classifier = s.read()

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": strict_classifier},
                {"role": "user", "content": question}
            ]
        )
        content = response.choices[0].message.content.strip()

        # Try parsing response JSON
        parsed = json.loads(content)
        domain = parsed.get("domain", "unknown")

        if domain not in ["user", "member", "transaction", "group", "unknown"]:
            print(f"WARNING: Invalid domain received: {domain}. Defaulting to 'unknown'.", flush=True)
            return "unknown"

        print("DEBUG: classified domain =", domain, flush=True)
        return domain
    
    except json.JSONDecodeError:
        print("ERROR: LLM did not return valid JSON. Defaulting to 'unknown'. Content:", content, flush=True)
        return "unknown"

    except Exception as e:
        print("ERROR: Unexpected classification error:", e, flush=True)
        return "unknown"



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
    domain = classify_question_domain(question)
    print("DEBUG: classified domain =", domain, flush=True)
    # Call Ai Convert question to SQL
    sql = generate_sql_from_question(question, domain)
    print("DEBUG: sql =", sql, flush=True)
    # Execute SQL
    executed = execute_sql(sql)
    print("DEBUG: executed =", executed, flush=True)
    # Call Ai to make it readable
    final_answer = format_readable_answer(question, executed)
    return final_answer