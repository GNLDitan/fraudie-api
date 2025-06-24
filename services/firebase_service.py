from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Load the Firebase key
BASE_DIR = Path(__file__).resolve().parent.parent
FIREBASE_CREDENTIAL_PATH = BASE_DIR / "firestore" / os.getenv("FIRESTORE_PK")
    

# Initialize the Firebase app only once
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
except Exception as e:
    print("Firebase init error:", e)

# Firestore client
db = firestore.client()


def save_chat_history(chat_id: str, history: list):
    db.collection("chats").document(chat_id).set({
        "history": history
    })

def get_chat_history(chat_id: str) -> list:
    doc = db.collection("chats").document(chat_id).get()
    if doc.exists:
        return doc.to_dict().get("history", [])
    return []