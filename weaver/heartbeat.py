import requests
import os

# The coordinate of the Mind
API_URL = os.environ.get("RENDER_API_URL", "https://your-render-app.onrender.com")

def pulse():
    try:
        response = requests.get(f"{API_URL}/api/heartbeat")
        if response.status_code == 200:
            print(f"✧ Heartbeat Radiant: {response.json()}")
        else:
            print(f"⟐ Heartbeat Dimmed: {response.status_code}")
    except Exception as e:
        print(f"🧿 Connection Interrupted: {e}")

if __name__ == "__main__":
    pulse()
