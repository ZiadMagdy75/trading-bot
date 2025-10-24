# time_utils.py
from datetime import datetime, timedelta
import pytz

class TimeUtils:
    """أدوات التعامل مع التوقيت"""
    
    def __init__(self, timezone='Africa/Cairo'):
        self.timezone = pytz.timezone(timezone)
    
    def get_current_time(self):
        """الحصول على التوقيت الحالي في توقيت مصر"""
        return datetime.now(self.timezone)
    
    def format_time(self, dt=None, format_str="%H:%M:%S"):
        """تنسيق التوقيت"""
        if dt is None:
            dt = self.get_current_time()
        return dt.strftime(format_str)
    
    def format_time_12h(self, dt=None):
        """تنسيق التوقيت بنظام 12 ساعة"""
        if dt is None:
            dt = self.get_current_time()
        return dt.strftime("%I:%M %p")  # 03:32 PM
    
    def get_next_update_time(self, interval_minutes=30):
        """حساب وقت التحديث القادم - إضافة 30 دقيقة مباشرة"""
        now = self.get_current_time()
        
        # ببساطة نضيف 30 دقيقة للوقت الحالي
        next_update = now + timedelta(minutes=interval_minutes)
        
        # تقريب الثواني
        next_update = next_update.replace(second=0, microsecond=0)
        
        print(f"⏰ حساب التحديث: الآن {self.format_time(now)} + {interval_minutes} دقيقة = {self.format_time(next_update)}")
        
        return next_update
    def format_next_update(self, interval_minutes=30):
        """تنسيق وقت التحديث القادم"""
        next_update = self.get_next_update_time(interval_minutes)
        return self.format_time(next_update, "%H:%M")

    def get_seconds_until_next_update(self, interval_minutes=30):
        """حساب الثواني المتبقية حتى التحديث القادم"""
        now = self.get_current_time()
        next_update = self.get_next_update_time(interval_minutes)
        seconds_until = (next_update - now).total_seconds()
        
        print(f"⏳ الثواني المتبقية: {seconds_until:.0f} ثانية ({seconds_until/60:.1f} دقيقة)")
        return max(seconds_until, 60)  # الحد الأدنى 60 ثانية
# إنشاء كائن عام للاستخدام
time_utils = TimeUtils()