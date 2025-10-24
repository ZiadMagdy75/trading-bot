# analysis.py
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import requests

class TechnicalAnalyzer:
    def __init__(self):
        self.period = "2d"
        self.interval = "30m"

        # إعداد جلسة requests مع User-Agent لتجنب رفض Yahoo
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        yf.utils.requests = self.session

    def get_stock_data(self, symbol):
        """جلب بيانات السهم مع معالجة الرموز الخاصة"""
        import json
        try:
            print(f"🔍 جلب بيانات: {symbol}")

            ticker = yf.Ticker(symbol, session=self.session)
            data = ticker.history(period=self.period, interval=self.interval)

            # fallback: API مباشر لو فشل yfinance
            if data is None or data.empty:
                print(f"⚠️ لا توجد بيانات من Yahoo، تجربة API بديل...")
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=30m&range=5d"
                r = self.session.get(url, timeout=10)
                chart = r.json()["chart"]["result"][0]
                timestamps = chart["timestamp"]
                close_prices = chart["indicators"]["quote"][0]["close"]
                df = pd.DataFrame({
                    "Datetime": pd.to_datetime(timestamps, unit="s"),
                    "Close": close_prices
                }).dropna()
                df.set_index("Datetime", inplace=True)
                data = df

            if data is None or data.empty:
                print(f"❌ لا توجد بيانات نهائيًا لـ {symbol}")
                return None

            print(f"✅ تم جلب {len(data)} صف لـ {symbol}")
            return data

        except Exception as e:
            print(f"❌ خطأ في جلب بيانات {symbol}: {e}")
            return None

    def get_symbol_name(self, symbol):
        name_map = {
            '^GSPC': 'S&P 500 Index',
            '^NDX': 'NASDAQ 100 Index',
            'NVDA': 'NVIDIA Corporation',
            'SPY': 'SPDR S&P 500 ETF',
            'QQQ': 'Invesco QQQ Trust',
            'GLD': 'SPDR Gold Trust',
            'TSLA': 'Tesla Inc'
        }
        return name_map.get(symbol, symbol)

    def calculate_trend_direction(self, data):
        if data is None or len(data) < 20:
            return "متردد 🔄"

        closes = data['Close']
        ma_short = closes.rolling(window=5).mean()
        ma_medium = closes.rolling(window=10).mean()
        ma_long = closes.rolling(window=20).mean()

        ma_short_last = ma_short.iloc[-1]
        ma_medium_last = ma_medium.iloc[-1]
        ma_long_last = ma_long.iloc[-1]
        current_price = closes.iloc[-1]

        momentum_5 = (closes.iloc[-1] - closes.iloc[-5]) / closes.iloc[-5] * 100 if len(closes) >= 5 else 0
        momentum_10 = (closes.iloc[-1] - closes.iloc[-10]) / closes.iloc[-10] * 100 if len(closes) >= 10 else 0

        if (ma_short_last > ma_medium_last > ma_long_last and
            current_price > ma_short_last and
            momentum_5 > 0.1 and momentum_10 > 0.1):
            return "صاعد 📈"
        elif (ma_short_last < ma_medium_last < ma_long_last and
              current_price < ma_short_last and
              momentum_5 < -0.1 and momentum_10 < -0.1):
            return "هابط 📉"
        else:
            return "متردد 🔄"

    def get_trend_analysis(self, symbol):
        data = self.get_stock_data(symbol)
        if data is None or data.empty:
            return {
                'direction': "غير معروف ❓",
                'strength': "غير معروف",
                'current_price': 0,
                'ma_5': 0,
                'ma_20': 0,
                'symbol_name': self.get_symbol_name(symbol)
            }

        trend = self.calculate_trend_direction(data)
        current_price = data['Close'].iloc[-1]
        closes = data['Close']
        ma_5 = closes.rolling(window=5).mean().iloc[-1] if len(closes) >= 5 else current_price
        ma_20 = closes.rolling(window=20).mean().iloc[-1] if len(closes) >= 20 else current_price

        if trend == "صاعد 📈":
            strength = "قوي 💪" if current_price > ma_20 * 1.02 else "معتدل 🔸"
        elif trend == "هابط 📉":
            strength = "قوي 💪" if current_price < ma_20 * 0.98 else "معتدل 🔸"
        else:
            strength = "محايد ⚖️"

        return {
            'direction': trend,
            'strength': strength,
            'current_price': current_price,
            'ma_5': ma_5,
            'ma_20': ma_20,
            'symbol_name': self.get_symbol_name(symbol)
        }

    # 🔹 باقي الدوال اللي كانت ناقصة:

    def calculate_support_resistance(self, data, levels=3):
        if data is None or len(data) < 10:
            return [], []

        highs = data['High'] if 'High' in data else data['Close']
        lows = data['Low'] if 'Low' in data else data['Close']
        closes = data['Close']
        current_price = closes.iloc[-1]

        pivot_point = (highs.tail(1).iloc[0] + lows.tail(1).iloc[0] + closes.tail(1).iloc[0]) / 3
        r1 = (2 * pivot_point) - lows.tail(1).iloc[0]
        s1 = (2 * pivot_point) - highs.tail(1).iloc[0]

        fib_levels = self.calculate_fibonacci_levels(highs.max(), lows.min())

        resistances = sorted([r1, fib_levels[0.5], fib_levels[0.618], highs.max()])
        supports = sorted([s1, fib_levels[0.382], fib_levels[0.236], lows.min()], reverse=True)

        return supports[:levels], resistances[:levels]

    def calculate_fibonacci_levels(self, high, low):
        diff = high - low
        return {
            0.236: high - diff * 0.236,
            0.382: high - diff * 0.382,
            0.5: high - diff * 0.5,
            0.618: high - diff * 0.618,
            1.0: low
        }

    def generate_options_recommendation(self, symbol, current_price, supports, resistances):
        recs = []
        if resistances:
            call_strike = min(resistances, key=lambda x: abs(x - current_price))
            recs.append({
                'type': 'CALL 📈',
                'strike': call_strike,
                'premium': 'هجومي ⚡' if (call_strike - current_price) / current_price < 0.02 else 'متوسط 📊',
                'target': call_strike + (call_strike * 0.008),
                'stoploss': current_price - (current_price * 0.005)
            })
        if supports:
            put_strike = max(supports, key=lambda x: abs(x - current_price))
            recs.append({
                'type': 'PUT 📉',
                'strike': put_strike,
                'premium': 'هجومي ⚡' if (current_price - put_strike) / current_price < 0.02 else 'متوسط 📊',
                'target': put_strike - (put_strike * 0.008),
                'stoploss': current_price + (current_price * 0.005)
            })
        return recs
