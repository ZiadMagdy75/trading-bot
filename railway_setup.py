# railway_setup.py
import os
import ssl
import certifi
import time
import random

def setup_railway_environment():
    """إعداد بيئة Railway للتغلب على قيود الشبكة"""
    
    # إصلاح مشاكل SSL
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # إعداد متغيرات البيئة
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    
    # إعداد User-Agent مخصص
    os.environ['YFINANCE_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    print("✅ تم إعداد بيئة Railway")

def random_delay(min_seconds=2, max_seconds=5):
    """انتظار عشوائي لتجنب الحظر"""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"⏳ انتظار {delay:.1f} ثانية...")
    time.sleep(delay)

# استدعاء الإعداد عند الاستيراد
setup_railway_environment()