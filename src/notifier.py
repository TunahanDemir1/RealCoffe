import requests
import os
from dotenv import load_dotenv
load_dotenv()

def send_telegram_alert(message: str, bot_token: str = None, chat_id: str = None):
    """
    Belirtilen bot token ve chat id üzerinden Telegram mesajı atar.
    Ortam değişkenlerinden (Environment Variables) ya da parametrelerden beslenebilir.
    """
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        print("[Notifier Uyarı] Telegram token veya chat_id tanımlı değil. Bildirim atlanıyor.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram bildirimi başarıyla gönderildi!")
        else:
            print(f"Telegram API hatası: {res.text}")
    except Exception as e:
        print(f"Telegram bildirimi gönderilemedi: {e}")

if __name__ == "__main__":
    # Test mesajı
    send_telegram_alert("Kahve Takip Botu: Pipeline testi başarılı!")