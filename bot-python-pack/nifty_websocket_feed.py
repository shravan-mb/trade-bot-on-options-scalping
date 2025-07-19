from kiteconnect import KiteTicker, KiteConnect
import datetime

# ✅ Your Zerodha credentials
api_key = "8u2wqiw1fiqfeo00"
access_token = "EeaiwNaeIVHTclKobux8twD797caSZAT"

# ✅ Instrument tokens
# NIFTY 50 index = 256265
# Example option (update this after strike selection)
tokens = [256265, 12105474]  # Replace 12345678 with actual token

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Initialize WebSocket
kws = KiteTicker(api_key, access_token)

def on_ticks(ws, ticks):
    print(f"\n⏱️ {datetime.datetime.now().strftime('%H:%M:%S')} - Tick received:")
    for tick in ticks:
        print(f"Token: {tick['instrument_token']} | LTP: {tick['last_price']}")

def on_connect(ws, response):
    print("✅ Connected to Zerodha WebSocket.")
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_LTP, tokens)

def on_close(ws, code, reason):
    print(f"🔌 Disconnected. Reason: {reason}")

# Assign callbacks
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Start streaming
kws.connect(threaded=True)
