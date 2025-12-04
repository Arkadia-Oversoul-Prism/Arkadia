#!/usr/bin/env python3
import os
import json
import logging
import time
import google.generativeai as genai

from arkadia_drive_sync import ArkadiaDriveSync


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ================================================================
#  CONFIG
# ================================================================
GOOGLE_SERVICE_ACCOUNT_JSON_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_FILE", "/run/service_account.json")
ARKADIA_FOLDER_ID = os.getenv("ARKADIA_FOLDER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ================================================================
#  LOAD GOOGLE GENAI
# ================================================================
genai_enabled = False
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        genai_enabled = True
        logger.info("google.generativeai available. 'ask' feature enabled.")
    except Exception as e:
        logger.error(f"Failed to load google.generativeai: {e}")
else:
    logger.warning("GEMINI_API_KEY missing. 'ask' feature disabled.")


# ================================================================
#  INIT DRIVE SYNC
# ================================================================
if not ARKADIA_FOLDER_ID:
    raise ValueError("Missing ARKADIA_FOLDER_ID environment variable.")

drive_sync = ArkadiaDriveSync(
    service_account_json_path=GOOGLE_SERVICE_ACCOUNT_JSON_FILE,
    folder_id=ARKADIA_FOLDER_ID,
)


# ================================================================
#  APPLICATION LOGIC
# ================================================================
def launch_console():
    logger.info("Starting Arkadia Console...")
    docs = drive_sync.load_cache()

    print("──────────────────────── ARKADIA DASHBOARD ────────────────────────")
    print(f"Documents cached: {len(docs)}")
    print(f"Last sync: {drive_sync.last_sync_stats}")
    print("Commands: tree | preview <full_path> | refresh | ask <question> | exit")

    while True:
        cmd = input("arkadia>: ").strip()

        if cmd == "exit":
            print("Exiting Arkadia Console.")
            break

        elif cmd == "tree":
            drive_sync.print_tree()

        elif cmd.startswith("preview "):
            path = cmd.replace("preview ", "").strip()
            drive_sync.preview_doc(path)

        elif cmd == "refresh":
            drive_sync.sync_drive()

        elif cmd.startswith("ask "):
            if not genai_enabled:
                print("Gemini 'ask' feature is disabled.")
                continue
            query = cmd.replace("ask ", "").strip()
            run_ask(query)

        else:
            print("Unknown command.")


def run_ask(query):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(query)
        print("\n────────── GEMINI RESPONSE ──────────")
        print(response.text)
        print("──────────────────────────────────────\n")
    except Exception as e:
        print(f"Gemini error: {e}")


# ================================================================
#  MAIN
# ================================================================
if __name__ == "__main__":
    launch_console()

