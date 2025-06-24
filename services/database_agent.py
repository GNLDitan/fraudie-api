import openai
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# Load connection info
SQL_DRIVER = os.getenv("SQL_DRIVER")
SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

# Setup OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that translates English questions to SQL Server queries."},
            {"role": "user", "content": f"Convert to SQL: {question}"}
        ]
    )
    sql = response.choices[0].message.content.strip()
    print("Generated SQL:", sql, flush=True)
    return sql

# Execute SQL and return results
def execute_sql(query: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

# Combined: question -> SQL -> result
def ask(question: str):
    sql = generate_sql_from_question(question)
    return execute_sql(sql)