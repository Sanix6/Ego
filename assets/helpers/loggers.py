import os
from datetime import datetime

LOG_FILE = os.path.join("logs", "ws.log")


def write_log(message: str):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time}] {message}\n")