# scalping_candle_signal.py

import time
import pandas as pd
from kiteconnect import KiteConnect, KiteTicker
from datetime import datetime, timedelta
from option_token_utils import get_option_details, get_nearest_expiry
from telegram_send import send_telegram_alert

# Time control
from datetime import datetime, time as dtime

last_trade_time = None
cooldown_minutes = 5

TRADING_START = dtime(9, 20)
TRADING_END = dtime(15, 0)

# Zerodha credentials
api_key = "8u2wqiw1fiqfeo00"
access_token = "EeaiwNaeIVHTclKobux8twD797caSZAT"
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Constants
INDEX_TOKEN = 256265  # NIFTY 50
tokens = [INDEX_TOKEN]

# Storage for live ticks
tick_data = []
option_ltp = None
current_signal = None
active_trade = False
entry_price = 0
stoploss = 0
target = 0
trade_symbol = ""

# Signal config
SL_POINTS = 5
TARGET_POINTS = 10

TRAIL_TRIGGER = 5     # Profit trigger to start trailing (points)
TRAIL_STEP = 2          # Move SL every 5 points gained

# Telegram & expiry
# expiry = "25JUL"

# NEW — get latest expiry string from helper
expiry = get_nearest_expiry()
chat_id = "6138982558"

# Add at the top of your script
LOT_SIZE = 1  # Nifty 50 lot size for CE/PE options

# WebSocket callbacks
def on_ticks(ws, ticks):
    global tick_data, option_ltp, active_trade, entry_price, stoploss, target

    for tick in ticks:
        if tick['instrument_token'] == INDEX_TOKEN:
            now = datetime.now()
            tick_data.append({"time": now, "price": tick['last_price']})
            # print(f"NIFTY Tick: {tick['last_price']}")  # 🔍 Add this line
        else:
            option_ltp = tick['last_price']
            
            # Auto square-off logic
            if active_trade:
                now = datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                time_str = now.strftime("%H:%M")
                unrealized_profit = option_ltp - entry_price

                if option_ltp <= stoploss:
                    send_telegram(f"📤 *Exit Trade*: SL HIT ❌ at ₹{option_ltp}")
                    log_trade(date_str, time_str, current_signal, trade_symbol, entry_price, option_ltp, '❌')
                    active_trade = False

                elif option_ltp >= target:
                    send_telegram(f"📤 *Exit Trade*: Target HIT ✅ at ₹{option_ltp}")
                    log_trade(date_str, time_str, current_signal, trade_symbol, entry_price, option_ltp, '✅')
                    active_trade = False

                elif unrealized_profit >= TRAIL_TRIGGER:
                    # Shift SL to lock-in profit
                    new_sl = option_ltp - TRAIL_STEP
                    if new_sl > stoploss:
                        stoploss = new_sl
                        print(f"🔁 Trailing SL moved up to ₹{stoploss}")
                        send_telegram(f"🔁 *Trailing SL* updated to ₹{stoploss}")

def log_trade(date, time, signal, symbol, entry, exit_price, result):
    pnl = round(exit_price - entry, 2)
    row = [date, time, signal, symbol, entry, exit_price, result, pnl]
    file_exists = os.path.isfile("trade_log.csv")
    with open("trade_log.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Date", "Time", "Signal", "Symbol", "Entry", "Exit", "Result", "PnL"])
        writer.writerow(row)

def on_connect(ws, response):
    print("✅ WebSocket connected")
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_LTP, tokens)

def on_close(ws, code, reason):
    print("🔌 WebSocket closed", reason)

# Resample 1-min candle
def resample_to_1min(df):
    df.set_index("time", inplace=True)
    ohlc = df['price'].resample('1min').ohlc()
    df.reset_index(inplace=True)
    return ohlc.dropna()

# Basic EMA-RSI strategy
def check_signal(df):
    df['ema'] = df['close'].ewm(span=9).mean()
    df['rsi'] = compute_rsi(df['close'], 2)
    last = df.iloc[-1]

    print(f"🔎 Close: {last['close']:.2f}, EMA: {last['ema']:.2f}, RSI: {last['rsi']:.2f}")

    if last['close'] > last['ema'] and last['rsi'] > 55:
        return "BUY_CE"
    elif last['close'] < last['ema'] and last['rsi'] < 45:
        return "BUY_PE"
    return None

def compute_rsi(series, period):
    delta = series.diff().dropna()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Trade execution logic
def place_trade(signal):
    global active_trade, entry_price, stoploss, target, option_ltp, tokens, trade_symbol

    # Get live NIFTY spot price
    spot = kite.ltp("NSE:NIFTY 50")['NSE:NIFTY 50']['last_price']

    # Get updated option token and symbol based on signal
    option_token, trade_symbol = get_option_details(spot, signal, expiry)

    if not option_token:
        print("⚠️ Option token not found. Skipping trade.")
        return

    # Unsubscribe previous option tokens except NIFTY index
    for t in tokens[:]:
        if t != INDEX_TOKEN:
            kws.unsubscribe([t])
            tokens.remove(t)
          
    # Subscribe to the new CE/PE token
    tokens.append(option_token)
    kws.subscribe([option_token])
    kws.set_mode(kws.MODE_LTP, [option_token])

    # Wait 1 second for LTP to arrive
    time.sleep(1)

    if option_ltp is None or option_ltp == 0:
        print("⚠️ LTP not available yet.")
        return
    
    try:
        # ✅ Place BUY MARKET ORDER
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=trade_symbol,
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=LOT_SIZE,
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_MIS
        )

        # Set trade state
        entry_price = option_ltp
        stoploss = entry_price - SL_POINTS
        target = entry_price + TARGET_POINTS
        active_trade = True

        # Telegram alert
        send_telegram(
            f"📥 *Order Placed*: `{signal}` on `{trade_symbol}`\n"
            f"🆔 Order ID: {order_id}\n"
            f"💰 Entry: ₹{entry_price}\n"
            f"🎯 Target: ₹{target}\n"
            f"🛑 Stoploss: ₹{stoploss}"
        )

        print(f"✅ Order placed successfully: {order_id}")

    except Exception as e:
        print(f"❌ Order placement failed: {e}")
        send_telegram(f"❌ *Order Failed*: `{trade_symbol}`\nError: {e}")

# Start WebSocket
kws = KiteTicker(api_key, access_token)
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close
print("🔄 Connecting to Kite WebSocket...")
kws.connect(threaded=True)

# Main loop
while True:
    try:
        if len(tick_data) >= 20:
            df = pd.DataFrame(tick_data)
            ohlc = resample_to_1min(df)
            print("🔍 1-Min Candle:")
            print(ohlc.tail(2))  # Show last 2 candles for inspection
            signal = check_signal(ohlc)

            # ✅ Time-based guard
            now = datetime.now()
            if not (TRADING_START <= now.time() <= TRADING_END):
                print("⏱ Outside trading hours, skipping...")
                tick_data = []
                time.sleep(10)
                continue

            # ✅ Cooldown check
            if signal and not active_trade:
                if last_trade_time and (now - last_trade_time).seconds < cooldown_minutes * 60:
                    print(f"⏳ Cooldown active. Waiting...")
                else:
                    place_trade(signal)
                    last_trade_time = now

            tick_data = []  # Clear after signal
        time.sleep(5)

    except KeyboardInterrupt:
        print("🛑 Exiting...")
        break
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(5)  # Retry delay
