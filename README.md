# trade-bot-on-options-scalping

This is a fully automated intraday scalping bot built for NIFTY 50 options trading using Zerodha's Kite Connect API. The bot analyzes 3-minute candlestick data, generates buy/sell signals based on price action, EMA, and RSI, and places auto trades on CE/PE options with a 1:2 or 1:3 risk-reward strategy. Live trade alerts are also sent to Telegram in real time.

Features:

- Zerodha Kite API integration for live data & order placement
- Signal generation using:
  - 3-minute candles
  - EMA-20 and RSI-14
  - Breakout/Reversal + Divergence logic
- Auto entry/exit on NIFTY options (CE/PE)
- Real-time Telegram alerts with trade info
- Risk management: 1:2 or 1:3 RR, SL/Target automation
- Option token auto-selection based on ATM strike
- WebSocket integration for tick data
- Modular & scalable code (Python)

Technologies

- Python 3.x
- Zerodha Kite Connect API
- WebSockets
- Telegram Bot API
- Pandas, NumPy, TA-Lib (optional)

Use Cases

- Scalping NIFTY options (intraday)
- Real-time trade signals & alerts
- Personal trading assistant
- Strategy backtesting & improvement
