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
        """حساب وقت التحديث القادم - على أوقات 00 و 30"""
        now = self.get_current_time()
        
        # حساب أقرب 00 أو 30 قادم
        current_minute = now.minute
        
        if current_minute < 30:
            # إذا الدقائق أقل من 30، التحديث القادم على 30
            minutes_to_next = 30 - current_minute
        else:
            # إذا الدقائق أكثر من 30، التحديث القادم على 00 من الساعة الجاية
            minutes_to_next = 60 - current_minute
        
        next_update = now + timedelta(minutes=minutes_to_next)
        next_update = next_update.replace(second=0, microsecond=0)
        
        print(f"⏰ حساب التحديث: الآن {self.format_time(now)} - التحديث بعد {minutes_to_next} دقيقة - الساعة {self.format_time(next_update)}")
        
        return next_update
        
    def format_next_update(self, interval_minutes=30):
        """تنسيق وقت التحديث القادم"""
        next_update = self.get_next_update_time(interval_minutes)
        return self.format_time(next_update, "%H:%M")

# إنشاء كائن عام للاستخدام
time_utils = TimeUtils()