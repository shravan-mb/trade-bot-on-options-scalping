import pandas as pd
from datetime import datetime

# Load instrument list once globally
instrument_df = pd.read_csv("instruments.csv")
nifty_opts = instrument_df[
    (instrument_df["exchange"] == "NFO") &
    (instrument_df["name"] == "NIFTY") &
    (instrument_df["segment"] == "NFO-OPT")
]

def get_option_details(nifty_spot, signal, expiry="25JUL"):
    """
    Return instrument token and symbol for nearest ATM strike.
    """
    strike = round(nifty_spot / 50) * 50
    option_type = "CE" if signal == "BUY_CE" else "PE"
    symbol = f"NIFTY{expiry}{strike}{option_type}"

    row = nifty_opts[nifty_opts["tradingsymbol"] == symbol]
    if not row.empty:
        token = int(row.iloc[0]["instrument_token"])
        return token, symbol
    else:
        print(f"❌ Option symbol not found: {symbol}")
        return None, None

def get_nearest_expiry():
    df = pd.read_csv("instruments.csv")

    # Filter for NIFTY weekly options
    df = df[(df['name'] == 'NIFTY') & (df['segment'] == 'NFO-OPT')]

    # Convert expiry to datetime
    df['expiry'] = pd.to_datetime(df['expiry'], errors='coerce')

    # Filter to future dates only
    today = datetime.now()
    future_expiries = df[df['expiry'] > today]

    # Get the nearest expiry
    nearest = future_expiries['expiry'].min()

    # Format it to Zerodha required format: e.g., "24JUL"
    expiry_str = nearest.strftime("%d%b").upper()
    return expiry_str