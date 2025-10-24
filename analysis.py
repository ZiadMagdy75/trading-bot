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
        # تمرير الجلسة إلى yfinance
        yf.utils.requests = self.session

    def get_stock_data(self, symbol):
        """جلب بيانات السهم مع معالجة الرموز الخاصة"""
        import json
        try:
            print(f"🔍 جلب بيانات: {symbol}")
            
            ticker = yf.Ticker(symbol, session=self.session)
            data = ticker.history(period=self.period, interval=self.interval)

            if data is None or data.empty:
                print(f"⚠️ لا توجد بيانات من Yahoo، تجربة API بديل...")

                # ✅ استخدام API مجاني بديل (RapidAPI Yahoo Finance)
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
        """الحصول على الاسم الكامل للسهم"""
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
        """تحديد اتجاه السهم (صاعد/هابط/متردد)"""
        if data is None or len(data) < 20:
            return "متردد 🔄"

        closes = data['Close']
        ma_short = closes.rolling(window=5).mean()
        ma_medium = closes.rolling(window=10).mean()
        ma_long = closes.rolling(window=20).mean()

        if len(ma_short) < 20 or len(ma_medium) < 20 or len(ma_long) < 20:
            return "متردد 🔄"

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
        """تحليل مفصل للاتجاه"""
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

    def get_live_trading_data(self, symbol):
        """جلب بيانات التداول الحية مع معالجة المؤشرات"""
        try:
            print(f"🔍 جلب بيانات حية لـ: {symbol}")
            ticker = yf.Ticker(symbol, session=self.session)
            info = ticker.info
            history = ticker.history(period='1d', interval='1m')

            if history.empty:
                print(f"❌ لا توجد بيانات تاريخية لـ {symbol}")
                return None

            current_price = history['Close'].iloc[-1]
            volume = history['Volume'].iloc[-1] if 'Volume' in history and not pd.isna(history['Volume'].iloc[-1]) else 0
            is_index = symbol.startswith('^')

            return (self._handle_index_data(symbol, current_price, volume, info)
                    if is_index else self._handle_stock_data(symbol, current_price, volume, info))

        except Exception as e:
            print(f"❌ خطأ في جلب البيانات الحية لـ {symbol}: {e}")
            return self._get_fallback_data(symbol)

    def _handle_index_data(self, symbol, current_price, volume, info):
        spread = current_price * 0.0001
        return {
            'symbol': symbol,
            'symbol_name': self.get_symbol_name(symbol),
            'current_price': round(current_price, 2),
            'bid_price': round(current_price - spread, 2),
            'ask_price': round(current_price + spread, 2),
            'bid_size': 1000,
            'ask_size': 1000,
            'volume': volume,
            'change': round(info.get('regularMarketChange', 0), 2),
            'change_percent': round(info.get('regularMarketChangePercent', 0), 2),
            'day_high': info.get('dayHigh', current_price * 1.005),
            'day_low': info.get('dayLow', current_price * 0.995),
            'previous_close': info.get('regularMarketPreviousClose', current_price),
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'is_index': True
        }

    def _handle_stock_data(self, symbol, current_price, volume, info):
        spread = current_price * 0.0005
        return {
            'symbol': symbol,
            'symbol_name': self.get_symbol_name(symbol),
            'current_price': round(current_price, 2),
            'bid_price': round(current_price - spread, 2),
            'ask_price': round(current_price + spread, 2),
            'bid_size': np.random.randint(100, 5000),
            'ask_size': np.random.randint(100, 5000),
            'volume': volume,
            'change': round(info.get('regularMarketChange', current_price * 0.01), 2),
            'change_percent': round(info.get('regularMarketChangePercent', 0.1), 2),
            'day_high': info.get('dayHigh', current_price * 1.02),
            'day_low': info.get('dayLow', current_price * 0.98),
            'previous_close': info.get('regularMarketPreviousClose', current_price),
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'is_index': False
        }

    def _get_fallback_data(self, symbol):
        """بيانات احتياطية إذا فشل المصدر الرئيسي"""
        try:
            ticker = yf.Ticker(symbol, session=self.session)
            history = ticker.history(period='1d', interval='1m')
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                return {
                    'symbol': symbol,
                    'symbol_name': self.get_symbol_name(symbol),
                    'current_price': round(current_price, 2),
                    'bid_price': round(current_price - 0.01, 2),
                    'ask_price': round(current_price + 0.01, 2),
                    'bid_size': 500,
                    'ask_size': 500,
                    'volume': 0,
                    'change': 0.0,
                    'change_percent': 0.0,
                    'day_high': current_price * 1.01,
                    'day_low': current_price * 0.99,
                    'previous_close': current_price,
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'is_index': symbol.startswith('^')
                }
        except:
            pass
        return None

    def get_next_update_time(self):
        now = datetime.now()
        next_update = now.replace(minute=(now.minute // 30) * 30) + pd.Timedelta(minutes=30)
        return next_update.strftime("%H:%M")
