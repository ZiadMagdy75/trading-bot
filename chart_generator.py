# chart_generator.py
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display
import matplotlib.font_manager as fm
from datetime import datetime

def reshape_arabic_text(text):
    """تعديل النص العربي ليظهر بشكل صحيح"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    except:
        return text

def create_professional_chart(symbol, data, supports, resistances, trend_info):
    """
    رسم بياني محترف مع مؤشر الاتجاه
    """
    try:
        # إعداد الخطوط للعربية
        try:
            # البحث عن خط يدعم العربية
            arabic_fonts = ['Arial', 'DejaVu Sans', 'Times New Roman', 'Segoe UI']
            for font in arabic_fonts:
                if font in [f.name for f in fm.fontManager.ttflist]:
                    plt.rcParams['font.family'] = font
                    break
        except:
            pass

        # إعداد الخلفية السوداء
        plt.rcParams['figure.facecolor'] = '#000000'
        plt.rcParams['axes.facecolor'] = '#000000'
        plt.rcParams['savefig.facecolor'] = '#000000'
        plt.rcParams['text.color'] = '#ffffff'
        plt.rcParams['axes.labelcolor'] = '#ffffff'
        plt.rcParams['xtick.color'] = '#ffffff'
        plt.rcParams['ytick.color'] = '#ffffff'
        plt.rcParams['grid.color'] = '#333333'

        # إنشاء ستايل مخصص
        mc = mpf.make_marketcolors(
            up='#00ff00',      # أخضر فاتح
            down='#ff0000',    # أحمر
            edge={'up':'#00ff00', 'down':'#ff0000'},
            wick={'up':'#00ff00', 'down':'#ff0000'}
        )

        style = mpf.make_mpf_style(
            base_mpl_style='dark_background',
            marketcolors=mc,
            gridstyle='--',
            gridcolor='#444444',
            facecolor='#000000',
            edgecolor='#666666',
            figcolor='#000000',
            y_on_right=False
        )

        add_plots = []
        
        # إضافة مستويات الدعم
        support_colors = ['#0080ff', '#0066cc', '#004d99']
        for i, support in enumerate(supports[:3]):
            add_plots.append(
                mpf.make_addplot([support] * len(data), 
                               color=support_colors[i], 
                               linestyle='--',
                               width=2.0,
                               alpha=0.8)
            )
        
        # إضافة مستويات المقاومة
        resistance_colors = ['#ff4444', '#cc0000', '#990000']
        for i, resistance in enumerate(resistances[:3]):
            add_plots.append(
                mpf.make_addplot([resistance] * len(data), 
                               color=resistance_colors[i], 
                               linestyle='--',
                               width=2.0,
                               alpha=0.8)
            )

        # إضافة المتوسطات المتحركة للاتجاه
        if len(data) > 20:
            ma_5 = data['Close'].rolling(window=5).mean()
            ma_20 = data['Close'].rolling(window=20).mean()
            
            add_plots.append(
                mpf.make_addplot(ma_5, color='#ff9900', width=1.5, alpha=0.7)
            )
            add_plots.append(
                mpf.make_addplot(ma_20, color='#ff00ff', width=1.5, alpha=0.7)
            )

        # إعداد خيارات الرسم بدون حجم
        plot_kwargs = {
            'type': 'candle',
            'style': style,
            'addplot': add_plots,
            'figsize': (14, 8),
            'returnfig': True,
            'volume': False,
            'title' :f'\n{trend_info["symbol_name"]} - 30 Minute Chart\n',
            'ylabel': 'Price ($)',
            'xlabel': 'Time',
            'tight_layout': True,
            'datetime_format': '%H:%M',
            'show_nontrading': False
        }

        # إنشاء الشارت
        fig, axes = mpf.plot(data, **plot_kwargs)

        # تخصيص المحاور
                # تخصيص المحاور
        ax_main = axes[0]

        # ⭐⭐ توسيع نطاق محور Y ليشمل كل المستويات ⭐⭐
        current_price = data['Close'].iloc[-1]
        
        # جمع كل مستويات الدعم والمقاومة
        all_levels = supports + resistances + [current_price]
        
        if all_levels:
            min_level = min(all_levels)
            max_level = max(all_levels)
            
            # حساب المدى وإضافة هامش 10%
            price_range = max_level - min_level
            y_min = min_level - (price_range * 0.10)  # هامش 10% من الأسفل
            y_max = max_level + (price_range * 0.10)  # هامش 10% من الأعلى
            
            # تطبيق النطاق الموسع على محور Y
            ax_main.set_ylim(y_min, y_max)
            print(f"📊 توسيع محور Y: {y_min:.2f} - {y_max:.2f}")

        # تحسين المظهر الرئيسي
        ax_main.set_facecolor('#000000')
        ax_main.grid(True, alpha=0.3, color='#444444')

        # تحسين المظهر الرئيسي
        ax_main.set_facecolor('#000000')
        ax_main.grid(True, alpha=0.3, color='#444444')
        
        # إضافة تسميات الدعم والمقاومة
        current_price = data['Close'].iloc[-1]
        
        for i, support in enumerate(supports[:3]):
            ax_main.axhline(y=support, color=support_colors[i], linestyle='--', alpha=0.8)
            # نص عربي مصحح
            support_text = reshape_arabic_text(f'دعم {i+1}: {support:.2f}')
            ax_main.text(
                0.02, support, f' {support_text}',
                transform=ax_main.get_yaxis_transform(),
                color=support_colors[i],
                fontsize=10,
                fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='#000000', 
                         edgecolor=support_colors[i], alpha=0.8)
            )

        for i, resistance in enumerate(resistances[:3]):
            ax_main.axhline(y=resistance, color=resistance_colors[i], linestyle='--', alpha=0.8)
            # نص عربي مصحح
            resistance_text = reshape_arabic_text(f'مقاومة {i+1}: {resistance:.2f}')
            ax_main.text(
                0.02, resistance, f' {resistance_text}',
                transform=ax_main.get_yaxis_transform(),
                color=resistance_colors[i],
                fontsize=10,
                fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='#000000', 
                         edgecolor=resistance_colors[i], alpha=0.8)
            )

        # إضافة مؤشر الاتجاه (نص عربي مصحح)
        trend_color = '#00ff00' if 'صاعد' in trend_info['direction'] else '#ff0000' if 'هابط' in trend_info['direction'] else '#ffff00'
        direction_text = reshape_arabic_text(f'الاتجاه: {trend_info["direction"]}')
        strength_text = reshape_arabic_text(f'القوة: {trend_info["strength"]}')
        price_text = reshape_arabic_text(f'السعر: {current_price:.2f}')
        
        ax_main.text(
            0.02, 0.95, direction_text,
            transform=ax_main.transAxes,
            color=trend_color,
            fontsize=12,
            fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='#333333', 
                     edgecolor=trend_color, alpha=0.9)
        )

        # إضافة قوة الاتجاه
        ax_main.text(
            0.02, 0.88, strength_text,
            transform=ax_main.transAxes,
            color='#ffffff',
            fontsize=10,
            fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='#222222', 
                     edgecolor='#666666')
        )

        # إضافة السعر الحالي
        ax_main.text(
            0.25, 0.95, price_text,
            transform=ax_main.transAxes,
            color='#ffffff',
            fontsize=11,
            fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='#333333', 
                     edgecolor='#ffffff')
        )

        # إضافة وقت التحديث
        update_time = datetime.now().strftime('%H:%M')
        time_text = reshape_arabic_text(f'الوقت: {update_time}')
        ax_main.text(
            0.85, 0.95, time_text,
            transform=ax_main.transAxes,
            color='#cccccc',
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='#222222', 
                     edgecolor='#666666')
        )

        # إضافة أوقات على الجانب الأيمن
        if len(data) > 0:
            times_to_show = []
            time_indices = [0, len(data)//4, len(data)//2, 3*len(data)//4, len(data)-1]
            
            for idx in time_indices:
                if idx < len(data):
                    time_str = data.index[idx].strftime('%H:%M')
                    price_val = data['Close'].iloc[idx]
                    times_to_show.append((time_str, price_val))
            
            for i, (time_str, price_val) in enumerate(times_to_show):
                ax_main.text(
                    0.98, price_val, f' {time_str}',
                    transform=ax_main.get_yaxis_transform(),
                    color='#aaaaaa',
                    fontsize=8,
                    ha='left',
                    va='center',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='#222222', 
                             edgecolor='#555555', alpha=0.7)
                )

        # حفظ الصورة
        buf = BytesIO()
        plt.savefig(
            buf, 
            format='png', 
            dpi=100,
            bbox_inches='tight',
            facecolor='#000000',
            edgecolor='none',
            pad_inches=0.1
        )
        buf.seek(0)
        plt.close()

        return buf

    except Exception as e:
        print(f"Error in professional chart: {e}")
        return create_fallback_chart(symbol, data, supports, resistances, trend_info)

def create_fallback_chart(symbol, data, supports, resistances, trend_info):
    """
    رسم بياني طارئ بدون حجم
    """
    try:
        # إعدادات أساسية
        plt.style.use('dark_background')
        fig, ax1 = plt.subplots(figsize=(13, 8), facecolor='black')
        
        # رسم البيانات
        dates = range(len(data))
        opens = data['Open'].values
        closes = data['Close'].values
        highs = data['High'].values
        lows = data['Low'].values
        
        # رسم الشموع
        for i, (open_val, close_val, high_val, low_val) in enumerate(zip(opens, closes, highs, lows)):
            color = 'green' if close_val >= open_val else 'red'
            
            # رسم الجسم
            body_bottom = min(open_val, close_val)
            body_height = abs(close_val - open_val)
            if body_height > 0:
                ax1.bar(i, body_height, bottom=body_bottom, 
                       color=color, width=0.6, alpha=0.8)
            
            # رسم الفتائل
            ax1.plot([i, i], [low_val, high_val], color=color, linewidth=1.5, alpha=0.8)
        
        current_price = closes[-1] if len(closes) > 0 else 0
        all_levels = supports + resistances + [current_price]
        
        if all_levels:
            min_level = min(all_levels)
            max_level = max(all_levels)
            price_range = max_level - min_level
            y_min = min_level - (price_range * 0.12)  # هامش 12%
            y_max = max_level + (price_range * 0.12)
            
            # تطبيق النطاق الموسع
            ax1.set_ylim(y_min, y_max)
            print(f"📊 توسيع محور Y (Fallback): {y_min:.2f} - {y_max:.2f}")
        # إضافة مستويات الدعم والمقاومة (نصوص عربية مصححة)
        for i, support in enumerate(supports[:3]):
            ax1.axhline(y=support, color='blue', linestyle='--', linewidth=2, alpha=0.8)
            support_text = reshape_arabic_text(f'دعم {i+1}: {support:.2f}')
            ax1.text(2, support, f' {support_text}', 
                    color='blue', fontweight='bold', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='black', edgecolor='blue'))
        
        for i, resistance in enumerate(resistances[:3]):
            ax1.axhline(y=resistance, color='red', linestyle='--', linewidth=2, alpha=0.8)
            resistance_text = reshape_arabic_text(f'مقاومة {i+1}: {resistance:.2f}')
            ax1.text(2, resistance, f' {resistance_text}', 
                    color='red', fontweight='bold', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='black', edgecolor='red'))
        
        # تخصيص المظهر
        ax1.set_facecolor('black')
        
        # العناوين والتسميات
        ax1.set_title(f'{symbol} - 30 Minute Chart', color='white', fontsize=14, fontweight='bold', pad=20)
        ax1.set_ylabel('Price ($) / Time', color='white', fontweight='bold', fontsize=11)
        ax1.set_xlabel('', color='white', fontweight='bold', fontsize=11)
        
        # إعداد المحاور
        ax1.tick_params(colors='white')
        ax1.grid(True, alpha=0.3, color='#444444')
        
        # إضافة مؤشر الاتجاه (نصوص عربية مصححة)
        trend_color = 'green' if 'صاعد' in trend_info['direction'] else 'red' if 'هابط' in trend_info['direction'] else 'yellow'
        direction_text = reshape_arabic_text(f'الاتجاه: {trend_info["direction"]}')
        ax1.text(0.02, 0.95, direction_text, 
                transform=ax1.transAxes, color=trend_color, fontweight='bold', fontsize=12,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='#333333', edgecolor=trend_color))
        
        # إضافة السعر الحالي
        current_price = closes[-1]
        price_text = reshape_arabic_text(f'السعر: {current_price:.2f}')
        ax1.text(0.25, 0.95, price_text, 
                transform=ax1.transAxes, color='white', fontweight='bold', fontsize=11,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='#333333', edgecolor='white'))
        
        # إضافة قوة الاتجاه
        strength_text = reshape_arabic_text(f'القوة: {trend_info["strength"]}')
        ax1.text(0.02, 0.88, strength_text,
                transform=ax1.transAxes, color='#ffffff', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='#222222', edgecolor='#666666'))
        
        # إضافة الوقت على الجانب الأيمن
        if len(data) > 0:
            # أخذ بعض النقاط الزمنية
            time_points = [0, len(data)//3, 2*len(data)//3, len(data)-1]
            
            for idx in time_points:
                if idx < len(data):
                    time_str = data.index[idx].strftime('%H:%M')
                    price_val = closes[idx]
                    ax1.text(0.98, price_val, f' {time_str}', 
                            transform=ax1.get_yaxis_transform(),
                            color='#aaaaaa', fontsize=8, ha='left', va='center',
                            bbox=dict(boxstyle="round,pad=0.2", facecolor='#222222', 
                                     edgecolor='#555555'))
        
        # إضافة وقت التحديث
        update_time = datetime.now().strftime('%H:%M')
        time_text = reshape_arabic_text(f'الوقت: {update_time}')
        ax1.text(0.85, 0.95, time_text, 
                transform=ax1.transAxes, color='#cccccc', fontsize=9,
                bbox=dict(boxstyle="round,pad=0.2", facecolor='#222222', edgecolor='#666666'))
        
        # ضبط المسافات
        plt.tight_layout()
        
        # حفظ الصورة
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', 
                   facecolor='black', edgecolor='none')
        buf.seek(0)
        plt.close()
        
        return buf
        
    except Exception as e:
        print(f"Error in fallback chart: {e}")
        return None