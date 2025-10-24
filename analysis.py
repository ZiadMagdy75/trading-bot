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
    
        # إعداد جلسة requests مع user-agent حقيقي
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        yf.utils.requests = self.session  # <=== إضافة هامة
    def get_stock_data(self, symbol):
        """جلب بيانات السهم مع معالجة الرموز الخاصة"""
        try:
            print(f"🔍 جلب بيانات: {symbol}")
            
            # استخدام الرمز مباشرة (لأن الرموز صحيحة الآن)
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=self.period, interval=self.interval)
            
            if data.empty:
                print(f"❌ لا توجد بيانات لـ {symbol}")
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
        
        # حساب المتوسطات المتحركة
        ma_short = closes.rolling(window=5).mean()   # متوسط قصير
        ma_medium = closes.rolling(window=10).mean() # متوسط متوسط
        ma_long = closes.rolling(window=20).mean()   # متوسط طويل
        
        if len(ma_short) < 20 or len(ma_medium) < 20 or len(ma_long) < 20:
            return "متردد 🔄"
        
        # آخر قيم للمتوسطات
        ma_short_last = ma_short.iloc[-1]
        ma_medium_last = ma_medium.iloc[-1]
        ma_long_last = ma_long.iloc[-1]
        
        # آخر سعر
        current_price = closes.iloc[-1]
        
        # حساب الزخم
        momentum_5 = (closes.iloc[-1] - closes.iloc[-5]) / closes.iloc[-5] * 100 if len(closes) >= 5 else 0
        momentum_10 = (closes.iloc[-1] - closes.iloc[-10]) / closes.iloc[-10] * 100 if len(closes) >= 10 else 0
        
        # تحديد الاتجاه بناءً على المتوسطات
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
        
        # حساب المتوسطات للتحليل
        closes = data['Close']
        ma_5 = closes.rolling(window=5).mean().iloc[-1] if len(closes) >= 5 else current_price
        ma_20 = closes.rolling(window=20).mean().iloc[-1] if len(closes) >= 20 else current_price
        
        # تحديد القوة
        if trend == "صاعد 📈":
            if current_price > ma_20 * 1.02:  # أعلى من المتوسط الطويل بـ 2%
                strength = "قوي 💪"
            else:
                strength = "معتدل 🔸"
        
        elif trend == "هابط 📉":
            if current_price < ma_20 * 0.98:  # أقل من المتوسط الطويل بـ 2%
                strength = "قوي 💪"
            else:
                strength = "معتدل 🔸"
        
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
            
            ticker = yf.Ticker(symbol)
            
            # جلب البيانات الأساسية
            info = ticker.info
            history = ticker.history(period='1d', interval='1m')
            
            if history.empty:
                print(f"❌ لا توجد بيانات تاريخية لـ {symbol}")
                return None
            
            # آخر سعر وحجم
            current_price = history['Close'].iloc[-1]
            volume = history['Volume'].iloc[-1] if 'Volume' in history and not pd.isna(history['Volume'].iloc[-1]) else 0
            
            # تحديد إذا كان المؤشر أو سهم عادي
            is_index = symbol.startswith('^')
            
            if is_index:
                # معالجة المؤشرات (مثل ^NDX, ^GSPC)
                return self._handle_index_data(symbol, current_price, volume, info)
            else:
                # معالجة الأسهم العادية
                return self._handle_stock_data(symbol, current_price, volume, info)
                
        except Exception as e:
            print(f"❌ خطأ في جلب البيانات الحية لـ {symbol}: {e}")
            return self._get_fallback_data(symbol)

    def _handle_index_data(self, symbol, current_price, volume, info):
        """معالجة بيانات المؤشرات"""
        # للمؤشرات ما فيش Bid/Ask, بنحسبها بناءً على السعر
        spread = current_price * 0.0001  # spread صغير للمؤشرات
        
        index_data = {
            'symbol': symbol,
            'symbol_name': self.get_symbol_name(symbol),
            'current_price': round(current_price, 2),
            'bid_price': round(current_price - spread, 2),
            'ask_price': round(current_price + spread, 2),
            'bid_size': 1000,  # حجم افتراضي
            'ask_size': 1000,
            'volume': volume,
            'change': round(info.get('regularMarketChange', 0), 2),
            'change_percent': round(info.get('regularMarketChangePercent', 0), 2),
            'day_high': info.get('dayHigh', current_price * 1.005),
            'day_low': info.get('dayLow', current_price * 0.995),
            'previous_close': info.get('regularMarketPreviousClose', current_price),
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'is_index': True  # علامة إنه مؤشر
        }
        return index_data

    def _handle_stock_data(self, symbol, current_price, volume, info):
        """معالجة بيانات الأسهم العادية"""
        # للأسهم العادية بنحاول نجيب بيانات حقيقية
        spread = current_price * 0.0005  # spread 0.05%
        
        stock_data = {
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
        return stock_data

    def _get_fallback_data(self, symbol):
        """بيانات احتياطية إذا فشل المصدر الرئيسي"""
        try:
            ticker = yf.Ticker(symbol)
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

    def format_trading_data(self, live_data):
        """تنسيق بيانات التداول مع معالجة المؤشرات"""
        if not live_data:
            return "⚠️ لا توجد بيانات متاحة"
        
        symbol = live_data['symbol']
        symbol_name = live_data['symbol_name']
        current_price = live_data['current_price']
        change = live_data['change']
        change_percent = live_data['change_percent']
        volume = live_data['volume']
        is_index = live_data.get('is_index', False)
        
        if is_index:
            # تنسيق خاص للمؤشرات
            bid_ask_text = """
📊 **المؤشرات لا تحتوي على عروض مباشرة**
💡 *يتم حساب العروض بناءً على تحليل السوق*
            """.strip()
        else:
            # تنسيق عادي للأسهم
            bid_ask_text = f"""
🔴 **Bid:** {live_data['bid_price']:.2f}  (Size: {live_data['bid_size']})
🟢 **Ask:** {live_data['ask_price']:.2f}  (Size: {live_data['ask_size']})
            """.strip()
        
        # تنسيق التغير
        change_icon = "🟢" if change_percent >= 0 else "🔴"
        change_text = f"{change_icon} **التغير:** {change:+.2f} ({change_percent:+.2f}%)"
        
        # تنسيق الحجم والنطاق السعري
        volume_text = f"📊 **الحجم:** {self.format_volume(volume)}" if volume > 0 else "📊 **الحجم:** غير متاح"
        range_text = f"📈 **النطاق:** {live_data['day_low']:.2f} - {live_data['day_high']:.2f}"
        
        # إضافة ملاحظة للمؤشرات
        index_note = "\n\n💡 *بيانات المؤشرات محسوبة - لا تحتوي على عروض مباشرة*" if is_index else ""
        
        formatted_text = f"""
📈 **{symbol_name} - بيانات التداول**

💰 **السعر الحالي:** {current_price:.2f}
{change_text}
{volume_text}
{range_text}

⚡ **العروض:**
{bid_ask_text}

🕒 **آخر تحديث:** {live_data['timestamp']}
{index_note}

💡 *بيانات محاكاة لأغراض تعليمية*
        """
        
        return formatted_text

    def format_volume(self, volume):
        """تنسيق الحجم بشكل مقروء"""
        if volume >= 1000000:
            return f"{volume/1000000:.2f}M"
        elif volume >= 1000:
            return f"{volume/1000:.2f}K"
        else:
            return f"{volume:.0f}"
    
    def calculate_support_resistance(self, data, levels=3):
        """حساب متقدم لمستويات الدعم والمقاومة"""
        if data is None or len(data) < 10:
            return [], []
        
        highs = data['High']
        lows = data['Low']
        closes = data['Close']
        current_price = closes.iloc[-1]
        
        print(f"🔍 تحليل الدعم/المقاومة للسعر: {current_price}")
        
        # طريقة 1: نقاط المحورية (Pivot Points)
        pivot_point = (highs.tail(1).iloc[0] + lows.tail(1).iloc[0] + closes.tail(1).iloc[0]) / 3
        r1 = (2 * pivot_point) - lows.tail(1).iloc[0]
        r2 = pivot_point + (highs.max() - lows.min())
        s1 = (2 * pivot_point) - highs.tail(1).iloc[0]
        s2 = pivot_point - (highs.max() - lows.min())
        
        # طريقة 2: أعلى وأقل المستويات الحديثة (فترة أطول)
        recent_high = highs.tail(50).max()  # زيادة الفترة لـ 50 شمعة
        recent_low = lows.tail(50).min()
        
        # طريقة 3: مستويات فيبوناتشي
        fib_levels = self.calculate_fibonacci_levels(recent_high, recent_low)
        
        # طريقة 4: المتوسطات المتحركة كمستويات ديناميكية
        ma_20 = closes.rolling(window=20).mean().iloc[-1]
        ma_50 = closes.rolling(window=50).mean().iloc[-1]
        
        # طريقة 5: مستويات تاريخية من البيانات
        historical_resistances = [
            highs.nlargest(3).values.tolist(),  # أعلى 3 قمم
            highs.quantile(0.75),               # الربع الثالث
            highs.mean()                        # متوسط القمم
        ]
        
        historical_supports = [
            lows.nsmallest(3).values.tolist(),  # أقل 3 قيعان
            lows.quantile(0.25),                # الربع الأول
            lows.mean()                         # متوسط القيعان
        ]
        
        # دمج جميع المستويات من الطرق المختلفة
        all_resistances = [
            r2, r1, 
            recent_high,
            fib_levels[0.618], fib_levels[0.5],
            ma_20 if ma_20 > current_price else None,
            ma_50 if ma_50 > current_price else None,
            *[r for r in historical_resistances[0] if r > current_price],
            historical_resistances[1] if historical_resistances[1] > current_price else None,
            historical_resistances[2] if historical_resistances[2] > current_price else None
        ]
        
        all_supports = [
            s1, s2,
            recent_low, 
            fib_levels[0.382], fib_levels[0.236],
            ma_20 if ma_20 < current_price else None,
            ma_50 if ma_50 < current_price else None,
            *[s for s in historical_supports[0] if s < current_price],
            historical_supports[1] if historical_supports[1] < current_price else None,
            historical_supports[2] if historical_supports[2] < current_price else None
        ]
        
        # تصفية القيم الفارغة والغير صالحة
        all_resistances = [r for r in all_resistances if r is not None and r > current_price]
        all_supports = [s for s in all_supports if s is not None and s < current_price]
        
        # إزالة التكرارات والتقريب
        all_resistances = list(dict.fromkeys([round(r, 2) for r in all_resistances]))
        all_supports = list(dict.fromkeys([round(s, 2) for s in all_supports]))
        
        # ترتيب المستويات
        resistance_levels = sorted(all_resistances)
        support_levels = sorted(all_supports, reverse=True)
        
        print(f"🎯 المقاومات المحتملة: {resistance_levels}")
        print(f"🛡️ الدعم المحتملة: {support_levels}")
        
        # إذا كانت المستويات قليلة، نضيف مستويات افتراضية بناءً على النسب المئوية
        if len(resistance_levels) < levels:
            additional_resistances = self.generate_additional_levels(current_price, 'resistance', levels - len(resistance_levels))
            resistance_levels.extend(additional_resistances)
            resistance_levels = sorted(resistance_levels)
        
        if len(support_levels) < levels:
            additional_supports = self.generate_additional_levels(current_price, 'support', levels - len(support_levels))
            support_levels.extend(additional_supports)
            support_levels = sorted(support_levels, reverse=True)
        
        # أخذ العدد المطلوب فقط
        final_resistances = resistance_levels[:levels]
        final_supports = support_levels[:levels]
        
        print(f"✅ المقاومات النهائية: {final_resistances}")
        print(f"✅ الدعم النهائي: {final_supports}")
        
        return final_supports, final_resistances

    def generate_additional_levels(self, current_price, level_type, count):
        """إنشاء مستويات إضافية بناءً على النسب المئوية"""
        levels = []
        percentages = [0.005, 0.01, 0.015, 0.02, 0.025]  # 0.5% إلى 2.5%
        
        for i in range(count):
            if i < len(percentages):
                if level_type == 'resistance':
                    level = current_price * (1 + percentages[i])
                else:  # support
                    level = current_price * (1 - percentages[i])
                levels.append(round(level, 2))
        
        return levels

    def calculate_fibonacci_levels(self, high, low):
        """حساب مستويات فيبوناتشي بدقة مع مستويات إضافية"""
        diff = high - low
        return {
            0.0: high,
            0.236: high - diff * 0.236,
            0.382: high - diff * 0.382, 
            0.5: high - diff * 0.5,
            0.618: high - diff * 0.618,
            0.786: high - diff * 0.786,
            1.0: low
        }
    
    def generate_options_recommendation(self, symbol, current_price, supports, resistances):
        """توليد توصيات متقدمة لعقود الأوبشن"""
        recommendations = []
        
        if resistances:
            call_strike = min(resistances, key=lambda x: abs(x - current_price))
            call_premium = "هجومي ⚡" if (call_strike - current_price) / current_price < 0.02 else "متوسط 📊"
            
            recommendations.append({
                'type': 'CALL 📈',
                'strike': call_strike,
                'premium': call_premium,
                'timeframe': 'اليوم',
                'target': call_strike + (call_strike * 0.008),
                'stoploss': current_price - (current_price * 0.005)
            })
        
        if supports:
            put_strike = max(supports, key=lambda x: abs(x - current_price))
            put_premium = "هجومي ⚡" if (current_price - put_strike) / current_price < 0.02 else "متوسط 📊"
            
            recommendations.append({
                'type': 'PUT 📉', 
                'strike': put_strike,
                'premium': put_premium, 
                'timeframe': 'اليوم',
                'target': put_strike - (put_strike * 0.008),
                'stoploss': current_price + (current_price * 0.005)
            })
        
        return recommendations
    
    def get_next_update_time(self):
        """حساب وقت التحديث القادم"""
        now = datetime.now()
        next_update = now.replace(minute=(now.minute // 30) * 30) + pd.Timedelta(minutes=30)
        return next_update.strftime("%H:%M")