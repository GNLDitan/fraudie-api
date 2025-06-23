import json
from pathlib import Path

CONFIG_DIR = Path("config")


def load_tool_schema(filename: str) -> dict:
    """
    Load a tool schema JSON file from the config directory.

    Args:
        filename (str): The name of the JSON file (e.g., 'record_user_details.json')

    Returns:
        dict: The loaded JSON schema as a Python dictionary
    """
    path = CONFIG_DIR / "tools" / filename

    if not path.exists():
        raise FileNotFoundError(f"Tool schema not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")
        
        
def load_template(filename: str, subFolder: str = "prompt") -> str:
    path = Path("config") / subFolder / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()