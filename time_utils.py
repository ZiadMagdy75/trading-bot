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
        """حساب وقت التحديث القادم بدقة"""
        now = self.get_current_time()
        
        # حساب الدقائق المتبوية للتحديث القادم
        current_minute = now.minute
        minutes_past_hour = current_minute % interval_minutes
        
        if minutes_past_hour == 0:
            # إذا كنا في بداية النص ساعة، التحديث القادم بعد 30 دقيقة
            minutes_to_next = interval_minutes
        else:
            # حساب كم دقيقة باقية للتحديث القادم
            minutes_to_next = interval_minutes - minutes_past_hour
        
        next_update = now + timedelta(minutes=minutes_to_next)
        
        print(f"⏰ حساب التحديث: الآن {self.format_time(now)} - التحديث بعد {minutes_to_next} دقيقة - الساعة {self.format_time(next_update)}")
        
        return next_update
        
    def format_next_update(self, interval_minutes=30):
        """تنسيق وقت التحديث القادم"""
        next_update = self.get_next_update_time(interval_minutes)
        return self.format_time(next_update, "%H:%M")

# إنشاء كائن عام للاستخدام
time_utils = TimeUtils()