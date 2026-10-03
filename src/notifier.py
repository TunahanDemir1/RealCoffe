import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_telegram_alert(message: str, bot_token: str = None, chat_id: str = None, parse_mode: str = "HTML"):
    """
    Belirtilen bot token ve chat id üzerinden Telegram mesajı atar.
    HTML parse mode özel karakter çakışmalarını önler (ör. ürün isimlerindeki altçizgiler).
    """
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        print("[Notifier Uyarı] Telegram token veya chat_id tanımlı değil. Bildirim atlanıyor.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }

    try:
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code == 200:
            print("Telegram bildirimi başarıyla gönderildi!")
            return True
        else:
            print(f"Telegram API hatası ({res.status_code}): {res.text}")
            # HTML hata verirse sade metin olarak göndermeyi dene
            if parse_mode:
                payload.pop("parse_mode", None)
                fallback_res = requests.post(url, json=payload, timeout=10)
                if fallback_res.status_code == 200:
                    print("Telegram bildirimi sade metin olarak iletildi.")
                    return True
            return False
    except Exception as e:
        print(f"Telegram bildirimi gönderilemedi: {e}")
        return False

if __name__ == "__main__":
    send_telegram_alert("<b>☕ Kahve Takip Botu:</b> Pipeline testi başarılı!")