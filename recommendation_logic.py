import yfinance as yf
import pandas as pd
import numpy as np

# --- Configuration ---
SMA_SHORT_PERIOD = 20
SMA_LONG_PERIOD = 50
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
BBANDS_PERIOD = 20
BBANDS_STD_DEV = 2
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

TARGET_SYMBOLS = [
    "COMI.CA", "SWDY.CA", "TMGH.CA", "EAST.CA", "MFPC.CA",
    "EGAL.CA", "ABUK.CA", "ALCN.CA", "QNBE.CA", "ETEL.CA"
]

# --- Technical Indicator Calculation ---
def calculate_indicators(df):
    close = df['Close']
    df[f'SMA_{SMA_SHORT_PERIOD}'] = close.rolling(window=SMA_SHORT_PERIOD).mean()
    df[f'SMA_{SMA_LONG_PERIOD}'] = close.rolling(window=SMA_LONG_PERIOD).mean()

    delta = close.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    rs = gain / loss.replace(0, 1e-10)
    df[f'RSI_{RSI_PERIOD}'] = 100 - (100 / (1 + rs))

    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_signal'] = df['MACD'].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']

    df['BB_Mid'] = close.rolling(window=BBANDS_PERIOD).mean()
    df['BB_Upper'] = df['BB_Mid'] + (close.rolling(window=BBANDS_PERIOD).std() * BBANDS_STD_DEV)
    df['BB_Lower'] = df['BB_Mid'] - (close.rolling(window=BBANDS_PERIOD).std() * BBANDS_STD_DEV)

    return df

# --- Recommendation Generator ---
def analyze_stock(symbol):
    result = {
        "symbol": symbol,
        "recommendation": "Error",
        "price": None,
        "sma_short": None,
        "sma_long": None,
        "rsi": None,
        "macd_hist": None,
        "bb_upper": None,
        "bb_lower": None,
        "outlook": None,
        "reasons": [],
        "error_message": None
    }

    try:
        df = yf.download(symbol, period="6mo", interval="1d")
        if df.empty or len(df) < SMA_LONG_PERIOD + 1:
            raise ValueError("Not enough data")

        df = calculate_indicators(df)
        latest = df.iloc[-1]

        price = float(latest['Close'])
        sma_short = float(latest[f'SMA_{SMA_SHORT_PERIOD}'])
        sma_long = float(latest[f'SMA_{SMA_LONG_PERIOD}'])
        rsi = float(latest[f'RSI_{RSI_PERIOD}'])
        macd_hist = float(latest['MACD_hist'])
        bb_upper = float(latest['BB_Upper'])
        bb_lower = float(latest['BB_Lower'])

        result.update({
            "price": price,
            "sma_short": sma_short,
            "sma_long": sma_long,
            "rsi": rsi,
            "macd_hist": macd_hist,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower
        })

        reasons = []
        if not np.isnan(sma_short) and not np.isnan(sma_long):
            if float(sma_short) > float(sma_long):
                reasons.append("SMA indicates bullish trend")
            else:
                reasons.append("SMA indicates bearish trend")

        if not np.isnan(rsi):
            if float(rsi) < RSI_OVERSOLD:
                reasons.append("RSI indicates oversold")
            elif float(rsi) > RSI_OVERBOUGHT:
                reasons.append("RSI indicates overbought")

        if not np.isnan(macd_hist):
            if float(macd_hist) > 0:
                reasons.append("MACD histogram is positive")
            else:
                reasons.append("MACD histogram is negative")

        if float(sma_short) > float(sma_long) and float(macd_hist) > 0:
            result['recommendation'] = "Strong Buy"
        elif float(sma_short) < float(sma_long) and float(macd_hist) < 0:
            result['recommendation'] = "Strong Sell"
        else:
            result['recommendation'] = "Hold"

        result['reasons'] = reasons

    except Exception as e:
        result['error_message'] = str(e)
        result['recommendation'] = "Error"
        result['reasons'] = [str(e)]

    return result

# --- Batch Recommendation Entry Point ---
def generate_recommendation_yf(symbol_or_list):
    if isinstance(symbol_or_list, str):
        return analyze_stock(symbol_or_list)
    elif isinstance(symbol_or_list, list):
        return [analyze_stock(sym) for sym in symbol_or_list]
    else:
        raise ValueError("Input must be a string or list of strings")

# --- Load Default Recommendations on Startup ---
def get_default_recommendations():
    return generate_recommendation_yf(TARGET_SYMBOLS)
