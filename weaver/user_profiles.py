import json
import os

USER_DB_FILE = "weaver/user_profiles.json"

def load_users():
    if not os.path.exists(USER_DB_FILE):
        return {}
    with open(USER_DB_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f, indent=2)

def add_user(node_id, username, model="gemini-2.5-flash", api_key=None):
    users = load_users()
    users[node_id] = {
        "username": username,
        "model": model,
        "api_key": api_key
    }
    save_users(users)

def get_user(node_id):
    users = load_users()
    return users.get(node_id, None)
