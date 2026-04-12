import requests
import hashlib
import json
import os

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

URL = "https://hoe.com.ua/page/pogodinni-vidkljuchennja"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "last_state.json"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    print("Telegram response:", response.text)


def send_telegram_photo(photo_url, caption=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    data = {"chat_id": CHAT_ID, "photo": photo_url, "caption": caption or ""}

    response = requests.post(url, data=data)
    print("Telegram response:", response.text)


def get_page_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(3000)

        # text before image (table)
        text_block = page.locator("h2 + p").first
        text = text_block.inner_text() if text_block.count() > 0 else ""

        # image (table)
        img = page.locator("h2 + p + p img").first
        img_url = img.get_attribute("src") if img.count() > 0 else None
        if img_url:
            full_img_url = img_url if img_url.startswith("http") else "https://hoe.com.ua" + img_url
        else:
            full_img_url = None

        browser.close()

        return text, full_img_url


def get_image_hash(img_url):
    if not img_url:
        return None

    response = requests.get(img_url, timeout=30)
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

    # text check
    if old_text != text:
        changed = True
        message_parts.append("📝 Є зміни в тексті:\n")
        message_parts.append(text[:1000])

    # image hash check
    if old_hash != img_hash:
        changed = True
        message_parts.append("\n📊 Графік оновлено")

    if changed:
        message = "⚡ Оновлення графіку відключень!\n\n" + "\n".join(message_parts)

        if img_url:
            send_telegram_photo(img_url, message)
        else:
            send_telegram(message)

    # save new state
    save_state({"text": text, "img_hash": img_hash})


if __name__ == "__main__":
    main()
