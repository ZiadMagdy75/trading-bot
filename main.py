# main.py
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TimedOut, NetworkError
from config import BOT_TOKEN, SYMBOLS, UPDATE_INTERVAL
from analysis import TechnicalAnalyzer
from chart_generator import create_professional_chart
import asyncio
import logging
from datetime import datetime, timedelta
import threading
import time

# 🔧 إضافة هذا السطر - إعداد بيئة Railway
try:
    from railway_setup import setup_railway_environment
    setup_railway_environment()
except ImportError:
    print("⚠️ إعدادات Railway غير متاحة - التشغيل المحلي")

# باقي الكود كما هو...
# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.analyzer = TechnicalAnalyzer()
        self.auto_chats = set()
        self.setup_handlers()
        
        # بدء نظام التحديث التلقائي
        self.start_auto_scheduler()
        
    def setup_handlers(self):
        """إعداد أوامر البوت"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("analyze", self.analyze_command))
        self.app.add_handler(CommandHandler("analysis", self.full_analysis))
        self.app.add_handler(CommandHandler("auto", self.auto_analysis))
        self.app.add_handler(CommandHandler("stop", self.stop_auto_analysis))
        self.app.add_handler(CommandHandler("live", self.live_trading_data))
        self.app.add_handler(CommandHandler("quote", self.live_trading_data))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("test", self.test_connection))

    async def test_connection(self, update: Update, context: CallbackContext):
        """اختبار اتصال البوت بالإنترنت"""
        try:
            import requests
            await update.message.reply_text("🔍 جاري اختبار الاتصال...")
            
            # انتظار عشوائي أولاً
            import time, random
            time.sleep(random.uniform(2, 4))
            
            # اختبار متعدد
            test_urls = [
                "https://www.google.com",
                "https://finance.yahoo.com",
                "https://query1.finance.yahoo.com/v8/finance/chart/SPY"
            ]
            
            results = []
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    results.append(f"{'✅' if response.status_code == 200 else '❌'} {url}: {response.status_code}")
                    time.sleep(1)  # انتظار بين الاختبارات
                except Exception as e:
                    results.append(f"❌ {url}: {str(e)}")
            
            report = "📊 **تقرير اختبار الاتصال:**\n\n" + "\n".join(results)
            await update.message.reply_text(report, parse_mode='Markdown')
                
        except Exception as e:
            await update.message.reply_text(f"❌ فشل الاختبار: {e}")
    
    
    async def start_command(self, update: Update, context: CallbackContext):
        """ترحيب بالعميل"""
        welcome_text = """
🎯 **مرحباً بك في بوت التحليل الفني المتقدم** 

📊 **الأوامر المتاحة:**
/start - عرض الرسالة الترحيبية
/analyze [رمز السهم] - تحليل سهم معين مع الرسم البياني
/analysis - تحليل جميع الأسهم مرة واحدة
/live [رمز السهم] - بيانات التداول الحية (Bid/Ask/Volume)
/auto - تفعيل التحديث التلقائي كل 30 دقيقة
/stop - إيقاف التحديث التلقائي
/status - عرض حالة النظام

⏰ **التحديث التلقائي:** كل 30 دقيقة

📈 **الأسهم المدعومة:**
S&P 500 (^GSPC), NASDAQ 100 (^NDX), NVDA, SPY, QQQ, GLD, TSLA

💡 **مميزات البوت:**
• 3 مستويات دعم ومقاومة
• تحليل اتجاه السهم (صاعد/هابط/متردد)
• رسوم بيانية متقدمة
• بيانات تداول حية (Bid/Ask)
• توصيات أوبشن هجومية
• تحديث تلقائي مستمر
"""
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: CallbackContext):
        """عرض حالة النظام"""
        chat_id = update.effective_chat.id
        auto_status = "مفعل ✅" if chat_id in self.auto_chats else "غير مفعل ❌"
        next_update = self.get_next_update_time()
        
        status_text = f"""
📊 **حالة النظام**

🔄 **التحديث التلقائي:** {auto_status}
👥 **المحادثات المفعلة:** {len(self.auto_chats)}
⏰ **التحديث القادم:** {next_update}
📈 **الأسهم المتابعة:** {len(SYMBOLS)}

💡 **الأوامر:**
/auto - تفعيل التحديث التلقائي
/stop - إيقاف التحديث التلقائي
"""
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def live_trading_data(self, update: Update, context: CallbackContext):
        """عرض بيانات التداول الحية"""
        if context.args:
            symbol = context.args[0].upper()
            if symbol not in SYMBOLS:
                await update.message.reply_text("❌ الرمز غير مدعوم. استخدم أحد الرموز التالية:\n" + "\n".join(SYMBOLS))
                return
        else:
            await update.message.reply_text("❌ يرجى تحديد رمز السهم. مثال:\n/live SPY")
            return
        
        await update.message.reply_text(f"🔄 جاري جلب بيانات {symbol}...")
        
        try:
            # جلب بيانات التداول الحية
            live_data = self.analyzer.get_live_trading_data(symbol)
            
            if live_data:
                # تنسيق البيانات بشكل جميل
                formatted_data = self.analyzer.format_trading_data(live_data)
                await update.message.reply_text(formatted_data, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ تعذر جلب بيانات التداول الحية")
                
        except Exception as e:
            logger.error(f"Error getting live data for {symbol}: {e}")
            await update.message.reply_text("❌ حدث خطأ في جلب البيانات الحية")
    
    async def analyze_symbol(self, symbol):
        """تحليل سهم معين مع تحسين الأداء"""
        try:
            # جلب البيانات
            data = self.analyzer.get_stock_data(symbol)
            if data is None or data.empty:
                return None, None, None, None, None, None
            
            current_price = data['Close'].iloc[-1]
            
            # حساب الدعم والمقاومة
            supports, resistances = self.analyzer.calculate_support_resistance(data)
            
            # حساب اتجاه السهم
            trend_info = self.analyzer.get_trend_analysis(symbol)
            
            # إنشاء الرسم البياني المحترف
            try:
                chart_buffer = create_professional_chart(symbol, data, supports, resistances, trend_info)
            except Exception as chart_error:
                logger.error(f"Chart error for {symbol}: {chart_error}")
                return None, supports, resistances, [], current_price, trend_info
            
            # توليد توصيات الأوبشن
            options_recommendations = self.analyzer.generate_options_recommendation(
                symbol, current_price, supports, resistances
            )
            
            return chart_buffer, supports, resistances, options_recommendations, current_price, trend_info
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None, [], [], [], None, {"direction": "متردد 🔄", "strength": "غير معروف", "symbol_name": symbol}
    
    async def analyze_command(self, update: Update, context: CallbackContext):
        """تحليل سهم محدد مع معالجة Timeout"""
        if context.args:
            symbol = context.args[0].upper()
            if symbol not in SYMBOLS:
                await update.message.reply_text("❌ الرمز غير مدعوم. استخدم أحد الرموز التالية:\n" + "\n".join(SYMBOLS))
                return
        else:
            await update.message.reply_text("❌ يرجى تحديد رمز السهم. مثال:\n/analyze SPY")
            return
        
        await update.message.reply_text(f"🔄 جاري تحليل {symbol}...")
        
        try:
            # تحليل السهم
            chart_buffer, supports, resistances, options, current_price, trend_info = await self.analyze_symbol(symbol)
            
            if chart_buffer is None:
                await update.message.reply_text("❌ حدث خطأ في تحليل السهم")
                return
            
            # إنشاء نص التقرير
            report_text = self.create_report_text(symbol, current_price, supports, resistances, options, trend_info)
            
            # محاولة إرسال الصورة مع Timeout
            try:
                await asyncio.wait_for(
                    update.message.reply_photo(
                        photo=InputFile(chart_buffer, filename=f'{symbol}_chart.png'),
                        caption=report_text,
                        parse_mode='Markdown'
                    ),
                    timeout=30.0  # 30 ثانية timeout
                )
                
            except asyncio.TimeoutError:
                await update.message.reply_text("⏰ انتهى الوقت المخصص لإرسال الصورة. جاري إرسال التقرير فقط...")
                await update.message.reply_text(report_text, parse_mode='Markdown')
                
            except TimedOut:
                await update.message.reply_text("⏰ انتهت مهلة الإرسال. جاري إرسال التقرير فقط...")
                await update.message.reply_text(report_text, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                await update.message.reply_text("⚠️ حدث خطأ في إرسال الصورة. جاري إرسال التقرير...")
                await update.message.reply_text(report_text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in analyze_command: {e}")
            await update.message.reply_text("❌ حدث خطأ غير متوقع في التحليل")
    
    async def full_analysis(self, update: Update, context: CallbackContext):
        """تحليل جميع الأسهم مع معالجة الأخطاء"""
        await update.message.reply_text("🔄 جاري تحليل جميع الأسهم... قد تستغرق بضع دقائق")
        
        successful_analysis = 0
        
        for symbol in SYMBOLS:
            try:
                chart_buffer, supports, resistances, options, current_price, trend_info = await self.analyze_symbol(symbol)
                
                if chart_buffer is not None:
                    report_text = self.create_report_text(symbol, current_price, supports, resistances, options, trend_info)
                    
                    try:
                        # إرسال مع timeout منفصل لكل سهم
                        await asyncio.wait_for(
                            update.message.reply_photo(
                                photo=InputFile(chart_buffer, filename=f'{symbol}_chart.png'),
                                caption=report_text,
                                parse_mode='Markdown'
                            ),
                            timeout=25.0
                        )
                        successful_analysis += 1
                        
                    except (asyncio.TimeoutError, TimedOut):
                        await update.message.reply_text(f"⏰ تم تخطي صورة {symbol} بسبب timeout")
                        await update.message.reply_text(report_text, parse_mode='Markdown')
                        successful_analysis += 1
                        
                    except Exception as e:
                        logger.error(f"Error sending {symbol} chart: {e}")
                        await update.message.reply_text(f"⚠️ تم تخطي صورة {symbol}")
                        await update.message.reply_text(report_text, parse_mode='Markdown')
                        successful_analysis += 1
                
                await asyncio.sleep(2)  # زيادة الوقت بين الإرسال
                
            except Exception as e:
                logger.error(f"Error in full analysis for {symbol}: {e}")
                await update.message.reply_text(f"❌ خطأ في تحليل {symbol}")
        
        await update.message.reply_text(f"✅ تم تحليل {successful_analysis} من {len(SYMBOLS)} أسهم بنجاح")
    
    async def auto_analysis(self, update: Update, context: CallbackContext):
        """تفعيل التحديث التلقائي"""
        chat_id = update.effective_chat.id
        
        if chat_id not in self.auto_chats:
            self.auto_chats.add(chat_id)
            print(f"✅ تم تفعيل التحديث التلقائي للمحادثة: {chat_id}")
            
            # إرسال رسالة تأكيد مع وقت التحديث القادم
            next_update = self.get_next_update_time()
            await update.message.reply_text(
                f"✅ **تم تفعيل التحديث التلقائي**\n\n"
                f"⏰ سيتم إرسال التقارير كل 30 دقيقة تلقائياً\n"
                f"📊 التحديث القادم: {next_update}\n"
                
                f"💡 لإيقاف التحديث: /stop",
                parse_mode='Markdown'
            )
            
            # إرسال تحليل فوري
            await self.send_auto_analysis(chat_id)
        else:
            await update.message.reply_text("⚠️ التحديث التلقائي مفعل بالفعل لهذه المحادثة")
    
    async def stop_auto_analysis(self, update: Update, context: CallbackContext):
        """إيقاف التحديث التلقائي"""
        chat_id = update.effective_chat.id
        
        if chat_id in self.auto_chats:
            self.auto_chats.remove(chat_id)
            print(f"❌ تم إيقاف التحديث التلقائي للمحادثة: {chat_id}")
            await update.message.reply_text(
                f"❌ **تم إيقاف التحديث التلقائي**\n\n"
                f"📊 لم تعد تتلقى تحديثات تلقائية\n"
                f"💡 لتفعيل التحديث: /auto",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("⚠️ التحديث التلقائي غير مفعل لهذه المحادثة")
    
    async def send_auto_analysis(self, chat_id):
        """إرسال التحليل التلقائي"""
        try:
            print(f"🔍 بدء التحليل التلقائي للمحادثة: {chat_id}")
            
            # إرسال رسالة بدء التحليل
            await self.app.bot.send_message(chat_id, "🔄 **بدء التحليل التلقائي**\nجاري تحليل جميع الأسهم...")
            
            successful_analysis = 0
            
            for symbol in SYMBOLS:
                try:
                    print(f"📊 جاري تحليل: {symbol}")
                    
                    chart_buffer, supports, resistances, options, current_price, trend_info = await self.analyze_symbol(symbol)
                    
                    if chart_buffer:
                        report_text = self.create_report_text(symbol, current_price, supports, resistances, options, trend_info)
                        
                        try:
                            await self.app.bot.send_photo(
                                chat_id=chat_id,
                                photo=InputFile(chart_buffer, filename=f'{symbol}_chart.png'),
                                caption=report_text,
                                parse_mode='Markdown'
                            )
                            successful_analysis += 1
                            print(f"✅ تم إرسال تحليل {symbol}")
                            
                        except Exception as e:
                            print(f"⚠️ خطأ في إرسال صورة {symbol}: {e}")
                            await self.app.bot.send_message(chat_id, report_text, parse_mode='Markdown')
                            successful_analysis += 1
                    else:
                        print(f"❌ فشل في تحليل {symbol}")
                    
                    # انتظار 3 ثوان بين كل سهم
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"❌ خطأ في تحليل {symbol}: {e}")
                    await self.app.bot.send_message(chat_id, f"❌ خطأ في تحليل {symbol}")
            
            # إرسال ملخص
            next_update = self.get_next_update_time()
            summary = (
                f"✅ **تم الانتهاء من التحليل التلقائي**\n\n"
                f"📊 تم تحليل {successful_analysis} من {len(SYMBOLS)} أسهم بنجاح\n"
                f"⏰ التحديث القادم: {next_update}\n\n"
                f"💡 لإيقاف التحديث: /stop"
            )
            await self.app.bot.send_message(chat_id, summary, parse_mode='Markdown')
            
            print(f"🎯 تم الانتهاء من التحليل التلقائي للمحادثة {chat_id}")
            
        except Exception as e:
            print(f"🚨 خطأ كبير في التحليل التلقائي: {e}")
            try:
                await self.app.bot.send_message(chat_id, "❌ حدث خطأ في التحليل التلقائي، جاري إعادة المحاولة في المرة القادمة")
            except:
                pass
    
    def start_auto_scheduler(self):
        """بدء الجدولة التلقائية بشكل صحيح"""
        def scheduler_loop():
            print("🔄 نظام التحديث التلقائي بدأ العمل...")
            counter = 0
            while True:
                try:
                    counter += 1
                    # الانتظار 30 دقيقة (1800 ثانية)
                    print(f"⏰ الانتظار {UPDATE_INTERVAL} دقيقة للتحديث القادم... (الدورة: {counter})")
                    time.sleep(UPDATE_INTERVAL * 60)  # 30 * 60 = 1800 ثانية
                    
                    if self.auto_chats:
                        print(f"🎯 وجد {len(self.auto_chats)} محادثة مفعلة، جاري الإرسال...")
                        
                        for chat_id in list(self.auto_chats):
                            try:
                                print(f"📤 إرسال تحليل تلقائي للمحادثة: {chat_id}")
                                # إنشاء event loop جديد لكل عملية
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(self.send_auto_analysis(chat_id))
                                loop.close()
                                print(f"✅ تم الإرسال بنجاح للمحادثة: {chat_id}")
                            except Exception as e:
                                print(f"❌ خطأ في إرسال التحليل لـ {chat_id}: {e}")
                    else:
                        print("ℹ️ لا توجد محادثات مفعلة للتحديث التلقائي")
                        
                except Exception as e:
                    print(f"🚨 خطأ في الجدولة: {e}")
                    time.sleep(60)  # الانتظار دقيقة ثم إعادة المحاولة
        
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
        print("✅ نظام التحديث التلقائي يعمل بنجاح!")
    
    def get_next_update_time(self):
        """حساب وقت التحديث القادم"""
        now = datetime.now()
        next_update = now.replace(minute=(now.minute // 30) * 30) + timedelta(minutes=30)
        return next_update.strftime("%H:%M")
    
    def create_report_text(self, symbol, current_price, supports, resistances, options, trend_info):
        """إنشاء نص التقرير مع شرح للمستويات"""
        support_text = "\n".join([f"{i+1}. {s:.2f}" for i, s in enumerate(supports)]) if supports else "📉 السعر قريب من قاع قوي"
        resistance_text = "\n".join([f"{i+1}. {r:.2f}" for i, r in enumerate(resistances)]) if resistances else "📈 السعر قريب من قمة قوية"
        
        # إضافة ملاحظة عن عدد المستويات
        levels_note = ""
        if len(supports) < 3 or len(resistances) < 3:
            levels_note = "\n💡 *ملاحظة: المستويات القليلة تشير إلى مناطق سعرية حرجة*"
        
        options_text = ""
        if options:
            for opt in options[:2]:
                options_text += f"• {opt['type']}: {opt['strike']:.2f} Strike\n"
                options_text += f"  📊 {opt['premium']} | 🎯 {opt['target']:.2f}\n"
    
        next_update = self.get_next_update_time()
        
        report = f"""
📈 **تحليل {trend_info['symbol_name']}**

🎯 **الاتجاه:** {trend_info['direction']} ({trend_info['strength']})

💰 **السعر الحالي:** `{current_price:.2f}`

🎯 **مستويات المقاومة:**
{resistance_text}

🛡️ **مستويات الدعم:**
{support_text}
{levels_note}

📊 **عقود الأوبشن المقترحة:**
{options_text if options_text else "• لا توجد توصيات متاحة حالياً"}

⏰ **التحديث القادم:** {next_update}


"""
        return report
    
    def run(self):
        """تشغيل البوت"""
        logger.info("🎯 Starting Enhanced Trading Bot...")
        
        print("🤖 البوت يعمل الآن...")
        print("💡 الأوامر المتاحة:")
        print("   /start - عرض التعليمات")
        print("   /auto - تفعيل التحديث التلقائي")
        print("   /stop - إيقاف التحديث التلقائي")
        print("   /status - عرض حالة النظام")
        
        self.app.run_polling(
            poll_interval=3.0,
            drop_pending_updates=True
        )

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()