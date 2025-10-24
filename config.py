# config.py
BOT_TOKEN = "7554758949:AAGPlcFoqEu5dkb11viXmInW0JFqqW92rh0"

# الأسهم والمؤشرات المطلوبة - الرموز الصحيحة لـ yfinance
SYMBOLS = ['^GSPC', '^NDX', 'NVDA', 'SPY', 'QQQ', 'GLD', 'TSLA']

# إعدادات التحليل
TIME_INTERVAL = '30m'
SUPPORT_RESISTANCE_LEVELS = 3

# إعدادات التحديث
UPDATE_INTERVAL = 30  # دقائق

# إعدادات الرسم البياني
CHART_STYLE = 'yahoo'
CHART_COLORS = {
    'up': '#26a69a',
    'down': '#ef5350',
    'support': '#2196F3',
    'resistance': '#FF5252',
    'ma20': '#FFA000'
}

# إعدادات التداول
RISK_PERCENTAGE = 0.5  # نسبة المخاطرة
TARGET_PERCENTAGE = 0.8  # نسبة الهدف
# إعدادات التوقيت
TIMEZONE = 'Africa/Cairo'  # توقيت مصر