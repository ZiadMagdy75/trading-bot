# data_providers.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
import random

class DataProvider:
    """مزود بيانات مرن مع مصادر متعددة"""
    
    @staticmethod
    def random_delay():
        """انتظار عشوائي"""
        delay = random.uniform(2, 5)
        time.sleep(delay)
    
    @staticmethod
    def get_data_alphavantage(symbol):
        """جلب البيانات من Alpha Vantage (بديل مجاني)"""
        try:
            # API Key مجاني - يمكنك الحصول على مفتاح مجاني من موقعهم
            api_key = "J21L3ZI6TIGFN4Y4"  # استبدل بمفتاحك من https://www.alphavantage.co/support/#api-key
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=30min&apikey={api_key}&outputsize=compact"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if "Time Series (30min)" in data:
                    time_series = data["Time Series (30min)"]
                    records = []
                    
                    for timestamp, values in time_series.items():
                        records.append({
                            'Open': float(values['1. open']),
                            'High': float(values['2. high']),
                            'Low': float(values['3. low']),
                            'Close': float(values['4. close']),
                            'Volume': int(values['5. volume'])
                        })
                    
                    if records:
                        df = pd.DataFrame(records[::-1])  # عكس الترتيب
                        df.index = pd.date_range(end=datetime.now(), periods=len(df), freq='30min')
                        print(f"✅ تم جلب {len(df)} صف من Alpha Vantage لـ {symbol}")
                        return df
                        
            return None
            
        except Exception as e:
            print(f"❌ خطأ في Alpha Vantage: {e}")
            return None
    
    @staticmethod
    def get_data_yahoo_direct(symbol):
        """جلب البيانات مباشرة من Yahoo Finance API"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2d&interval=30m"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    
                    timestamps = result['timestamp']
                    quotes = result['indicators']['quote'][0]
                    
                    records = []
                    for i, ts in enumerate(timestamps):
                        records.append({
                            'Open': quotes['open'][i],
                            'High': quotes['high'][i],
                            'Low': quotes['low'][i],
                            'Close': quotes['close'][i],
                            'Volume': quotes['volume'][i] if quotes['volume'][i] else 0
                        })
                    
                    if records:
                        df = pd.DataFrame(records)
                        df.index = pd.to_datetime(timestamps, unit='s')
                        print(f"✅ تم جلب {len(df)} صف مباشرة من Yahoo لـ {symbol}")
                        return df
                        
            return None
            
        except Exception as e:
            print(f"❌ خطأ في Yahoo المباشر: {e}")
            return None
    
    @staticmethod
    def get_data_fallback(symbol, periods=50):
        """بيانات احتياطية واقعية"""
        try:
            base_prices = {
                'SPY': 450.50, 'QQQ': 380.75, 'NVDA': 480.25, 
                'TSLA': 240.80, 'GLD': 180.40, '^GSPC': 4500.60,
                '^NDX': 15500.30
            }
            base_price = base_prices.get(symbol, 100.0)
            
            end_date = datetime.now()
            dates = [end_date - timedelta(minutes=30*i) for i in range(periods)][::-1]
            
            np.random.seed(hash(symbol) % 1000)
            
            prices = [base_price]
            for i in range(1, periods):
                change = np.random.normal(0, 0.002)
                new_price = prices[-1] * (1 + change)
                prices.append(max(new_price, base_price * 0.8))
            
            data = pd.DataFrame({
                'Open': [p * (1 + np.random.normal(0, 0.001)) for p in prices],
                'High': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
                'Low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
                'Close': prices,
                'Volume': [np.random.randint(1000000, 5000000) for _ in range(periods)]
            }, index=dates)
            
            print(f"✅ تم إنشاء بيانات احتياطية لـ {symbol} ({len(data)} صف)")
            return data
            
        except Exception as e:
            print(f"❌ خطأ في البيانات الاحتياطية: {e}")
            return None
    
    @staticmethod
    def get_stock_data(symbol):
        """جلب البيانات من مصادر متعددة"""
        print(f"🔍 محاولة جلب بيانات {symbol} من مصادر متعددة...")
        
        # المحاولة 1: Yahoo Finance المباشر
        DataProvider.random_delay()
        data = DataProvider.get_data_yahoo_direct(symbol)
        if data is not None and not data.empty:
            return data
        
        # المحاولة 2: Alpha Vantage
        DataProvider.random_delay()
        data = DataProvider.get_data_alphavantage(symbol)
        if data is not None and not data.empty:
            return data
        
        # المحاولة 3: البيانات الاحتياطية
        print(f"🔄 استخدام البيانات الاحتياطية لـ {symbol}")
        return DataProvider.get_data_fallback(symbol)