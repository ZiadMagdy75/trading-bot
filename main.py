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
        
    def setup_handlers(self):
        """إعداد أوامر البوت"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("analyze", self.analyze_command))
        self.app.add_handler(CommandHandler("analysis", self.full_analysis))
        self.app.add_handler(CommandHandler("auto", self.auto_analysis))
        self.app.add_handler(CommandHandler("stop", self.stop_auto_analysis))
        self.app.add_handler(CommandHandler("live", self.live_trading_data))
        self.app.add_handler(CommandHandler("quote", self.live_trading_data))
    
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
        
        ⚠️ **تحذير:** التحليلات لأغراض تعليمية فقط
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
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
            await update.message.reply_text("✅ تم تفعيل التحديث التلقائي كل 30 دقيقة")
            await self.send_auto_analysis(chat_id)
        else:
            await update.message.reply_text("⚠️ التحديث التلقائي مفعل بالفعل")
    
    async def stop_auto_analysis(self, update: Update, context: CallbackContext):
        """إيقاف التحديث التلقائي"""
        chat_id = update.effective_chat.id
        
        if chat_id in self.auto_chats:
            self.auto_chats.remove(chat_id)
            await update.message.reply_text("❌ تم إيقاف التحديث التلقائي")
        else:
            await update.message.reply_text("⚠️ التحديث التلقائي غير مفعل")
    
    async def send_auto_analysis(self, chat_id):
        """إرسال التحليل التلقائي"""
        try:
            await self.app.bot.send_message(chat_id, "🔄 بدء التحليل التلقائي لجميع الأسهم...")
            
            for symbol in SYMBOLS:
                chart_buffer, supports, resistances, options, current_price, trend_info = await self.analyze_symbol(symbol)
                
                if chart_buffer:
                    report_text = self.create_report_text(symbol, current_price, supports, resistances, options, trend_info)
                    
                    try:
                        await asyncio.wait_for(
                            self.app.bot.send_photo(
                                chat_id=chat_id,
                                photo=InputFile(chart_buffer, filename=f'{symbol}_chart.png'),
                                caption=report_text,
                                parse_mode='Markdown'
                            ),
                            timeout=20.0
                        )
                    except (asyncio.TimeoutError, TimedOut):
                        await self.app.bot.send_message(chat_id, f"⏰ تم تخطي صورة {symbol}")
                        await self.app.bot.send_message(chat_id, report_text, parse_mode='Markdown')
                    except Exception as e:
                        logger.error(f"Error sending auto analysis for {symbol}: {e}")
                        await self.app.bot.send_message(chat_id, report_text, parse_mode='Markdown')
                
                await asyncio.sleep(2)
                
            await self.app.bot.send_message(chat_id, f"✅ تم الانتهاء من التحليل التلقائي")
            
        except Exception as e:
            logger.error(f"Error in auto analysis for chat {chat_id}: {e}")
    
    def start_auto_scheduler(self):
        """بدء الجدولة التلقائية"""
        def scheduler_loop():
            while True:
                try:
                    time.sleep(UPDATE_INTERVAL * 60)
                    
                    if self.auto_chats:
                        logger.info(f"🔄 Sending auto analysis to {len(self.auto_chats)} chats")
                        
                        for chat_id in list(self.auto_chats):
                            future = asyncio.run_coroutine_threadsafe(
                                self.send_auto_analysis(chat_id), 
                                self.app._get_running_loop()
                            )
                            # لا حاجة للانتظار هنا - future يتم بشكل منفصل
                            
                except Exception as e:
                    logger.error(f"❌ Scheduler error: {e}")
                    time.sleep(60)
        
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
        logger.info("✅ Auto scheduler started successfully")
    
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

⚡️ **ملاحظة:** التوصيات لأغراض تعليمية فقط
        """
        return report
    
    def run(self):
        """تشغيل البوت"""
        logger.info("🎯 Starting Enhanced Trading Bot...")
        
        self.start_auto_scheduler()
        self.app.run_polling(
            poll_interval=3.0,  # تقليل فترة الاستطلاع
            drop_pending_updates=True  # تجاهل التحديثات المعلقة عند البدء
        )

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()