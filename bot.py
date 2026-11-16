import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# تفعيل نظام التنبيهات لمتابعة حالة البوت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة الرد عند إرسال أمر /start"""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"مرحباً بك يا {user_name} في ساحة لعبة XO Arena! 🎮\n"
        "البوت يعمل الآن بشكل آمن ومستقر. أرسل الأوامر للبدء."
    )

def main():
    # سحب التوكن تلقائياً من متغيرات البيئة في Railway
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت في متغيرات البيئة!")
        return

    # بناء وتشغيل تطبيق البوت
    app = ApplicationBuilder().token(TOKEN).build()

    # ربط أمر /start بالدالة الخاصة به
    app.add_handler(CommandHandler("start", start))

    print("XO ARENA - Running safely...")
    
    # بدء تشغيل البوت بنظام الاستماع المستمر
    app.run_polling()

if __name__ == '__main__':
    main()
