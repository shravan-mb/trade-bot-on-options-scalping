import requests

# Telegram credentials
BOT_TOKEN = "8029709691:AAHMBEEf93Thr-9GiqOXNuomHhOeSMM1iHo"
CHAT_ID = "6138982558"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("📩 Telegram alert sent.")
        else:
            print("⚠️ Telegram error:", response.text)
    except Exception as e:
        print("🚨 Failed to send Telegram alert:", e)
