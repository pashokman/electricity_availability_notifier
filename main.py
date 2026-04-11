import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
from dotenv import load_dotenv

load_dotenv()

URL = "https://hoe.com.ua/page/pogodinni-vidkljuchennja"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "last_state.json"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})


def get_page_data():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # find first image (table)
    img = soup.find("img")
    img_url = img["src"] if img else None

    # text before the first image
    text_blocks = []
    for tag in soup.find_all(["p", "div"]):
        if tag.find("img"):
            break
        text = tag.get_text(strip=True)
        if text:
            text_blocks.append(text)

    text_content = "\n".join(text_blocks)

    return text_content, img_url


def get_image_hash(img_url):
    if not img_url:
        return None

    if img_url.startswith("/"):
        img_url = "https://hoe.com.ua" + img_url

    response = requests.get(img_url)
    return hashlib.md5(response.content).hexdigest()


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main():
    state = load_state()

    text, img_url = get_page_data()
    img_hash = get_image_hash(img_url)

    old_text = state.get("text")
    old_hash = state.get("img_hash")

    changed = False
    message_parts = []

    # text hash check
    if old_text != text:
        changed = True
        message_parts.append("📝 Є зміни в тексті:\n")
        message_parts.append(text[:1000])  # щоб не було занадто довго

    # image hash check
    if old_hash != img_hash:
        changed = True
        message_parts.append("\n📊 Графік оновлено")

    if changed:
        message = "⚡ Оновлення графіку відключень!\n\n" + "\n".join(message_parts)
        send_telegram(message)

    # save new state
    save_state({"text": text, "img_hash": img_hash})


if __name__ == "__main__":
    main()

print(BOT_TOKEN)
print(CHAT_ID)
