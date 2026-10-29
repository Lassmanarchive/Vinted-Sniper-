import os
import requests

WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def send_test():
    if not WEBHOOK:
        print("Discord webhook saknas!")
        return

    message = {
        "content": "🔥 VINTED SNIPER ONLINE! Discord-kopplingen fungerar."
    }

    response = requests.post(WEBHOOK, json=message, timeout=15)
    print("Discord status:", response.status_code)

if __name__ == "__main__":
    send_test()
