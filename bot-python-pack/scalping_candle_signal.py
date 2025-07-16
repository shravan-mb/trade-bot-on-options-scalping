from kiteconnect import KiteConnect, KiteTicker
import pandas as pd
import datetime as dt
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

# ======================= CONFIGURATION ========================
api_key = "8u2wqiw1fiqfeo00"
access_token = "MqLW7DjAgQp45IsC7xF9z22uWNuFY7N4"
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

BOT_TOKEN = "8029709691:AAHMBEEf93Thr-9GiqOXNuomHhOeSMM1iHo"
CHAT_ID = "6138982558"

# NIFTY spot token + Option strike token
INDEX_TOKEN = 256265  # NIFTY 50
OPTION_TOKEN = 12105474  # Replace with your actual strike token
tokens = [INDEX_TOKEN, OPTION_TOKEN]

TRADE_SYMBOL = "NIFTY2571725200CE"  # Replace with your actual tradingsymbol
QTY = 50  # 1 Lot NIFTY
RR_RATIO = 3  # Risk-Reward 1:3
STOPLOSS_PCT = 0.3  # 30% stoploss
# =============================================================

kws = KiteTicker(api_key, access_token)
ohlc_data = {}
open_trade = None  # Track active trade details

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            print("\U0001F4E9 Telegram alert sent.")
        else:
            print("⚠️ Telegram Error:", r.text)
    except Exception as e:
        print("🚨 Telegram Error:", e)

def place_option_trade(signal):
    global open_trade
    try:
        print(f"🛒 Placing order for {TRADE_SYMBOL}...")
        ltp_data = kite.ltp(f"NFO:{TRADE_SYMBOL}")
        ltp = ltp_data[f"NFO:{TRADE_SYMBOL}"]['last_price']
        sl = round(ltp * (1 - STOPLOSS_PCT), 1)
        target = round(ltp + (ltp - sl) * RR_RATIO, 1)

        order = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=TRADE_SYMBOL,
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=QTY,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_MARKET
        )

        open_trade = {
            "entry": ltp,
            "sl": sl,
            "target": target,
            "active": True
        }

        send_telegram_alert(
            f"✅ Order Placed: {TRADE_SYMBOL}\nQty: {QTY}\nEntry: {ltp}\nSL: {sl}\nTarget: {target}"
        )
        print(f"✅ Order ID: {order}")

    except Exception as e:
        print("🚨 Order Failed:", e)
        send_telegram_alert(f"🚨 Order Failed: {e}")

def check_exit_conditions(ltp):
    global open_trade
    if open_trade and open_trade["active"]:
        sl = open_trade['sl']
        target = open_trade['target']

        if ltp <= sl:
            exit_order("SL HIT ❌", ltp)
        elif ltp >= target:
            exit_order("Target HIT ✅", ltp)

def exit_order(reason, exit_price):
    global open_trade
    try:
        kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=TRADE_SYMBOL,
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=QTY,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_MARKET
        )
        open_trade['active'] = False
        send_telegram_alert(f"📤 Exit Trade: {TRADE_SYMBOL}\n{reason}\nExit Price: {exit_price}")
        print(f"📤 Exited: {reason} at {exit_price}")
    except Exception as e:
        print("🚨 Exit Order Failed:", e)
        send_telegram_alert(f"🚨 Exit Order Failed: {e}")

def resample_to_3min(df):
    df.set_index('timestamp', inplace=True)
    df = df.resample('3min').agg({'ltp': ['first', 'max', 'min', 'last']})
    df.columns = ['open', 'high', 'low', 'close']
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df

def calculate_signals(df):
    df['ema'] = EMAIndicator(df['close'], 20).ema_indicator()
    df['rsi'] = RSIIndicator(df['close'], 14).rsi()
    latest = df.iloc[-1]

    if latest['close'] > latest['ema'] and latest['rsi'] > 55:
        return "BUY_CE"
    elif latest['close'] < latest['ema'] and latest['rsi'] < 45:
        return "BUY_PE"
    else:
        return None

def on_ticks(ws, ticks):
    global ohlc_data
    for tick in ticks:
        token = tick['instrument_token']
        ltp = tick['last_price']
        ts = dt.datetime.now().replace(second=0, microsecond=0)

        # ✅ Check if any active trade needs exit
        if token == OPTION_TOKEN:
            check_exit_conditions(ltp)

        if token not in ohlc_data:
            ohlc_data[token] = []

        ohlc_data[token].append({'timestamp': ts, 'ltp': ltp})

        if ts.minute % 3 == 0 and len(ohlc_data[token]) >= 10:
            df = pd.DataFrame(ohlc_data[token])
            ohlc = resample_to_3min(df)
            signal = calculate_signals(ohlc)

            print(f"\n📊 Token: {token} | Time: {ts.strftime('%H:%M')} | Signal: {signal}")
            if signal and (not open_trade or not open_trade["active"]):
                alert_msg = f"📈 {dt.datetime.now().strftime('%H:%M:%S')} - Signal: {signal}\n" \
                             f"Instrument: {OPTION_TOKEN}\nTimeframe: 3-min\n" \
                             f"Action: {'Buy Call Option' if signal == 'BUY_CE' else 'Buy Put Option'}"
                send_telegram_alert(alert_msg)
                place_option_trade(signal)

            ohlc_data[token] = []

def on_connect(ws, response):
    print("✅ WebSocket connected. Subscribing to tokens...")
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_LTP, tokens)

def on_close(ws, code, reason):
    print("🔌 WebSocket disconnected:", reason)

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

print("🔄 Connecting to Kite WebSocket...")
kws.connect(threaded=True)

# ✅ Keep the script alive
import time
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Manual exit")
        break
