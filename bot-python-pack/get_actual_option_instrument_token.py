from kiteconnect import KiteConnect
import pandas as pd

# Replace with your credentials
api_key = "8u2wqiw1fiqfeo00"
access_token = "MqLW7DjAgQp45IsC7xF9z22uWNuFY7N4"

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Download all NSE instruments
print("🔄 Downloading instruments...")
instruments = kite.instruments("NFO")

# Load into DataFrame for easy filtering
df = pd.DataFrame(instruments)

# Filter only NIFTY options
nifty_opts = df[
    (df['name'] == 'NIFTY') &
    (df['segment'] == 'NFO-OPT') &
    (df['expiry'] == df['expiry'].min())  # nearest expiry
]

# Optional: filter for CE or PE and a strike price range
strike = 25200
opt_type = 'CE'

filtered = nifty_opts[
    (nifty_opts['strike'] == strike) &
    (nifty_opts['instrument_type'] == opt_type)
]

print(filtered[['tradingsymbol', 'instrument_token', 'strike', 'expiry']])
