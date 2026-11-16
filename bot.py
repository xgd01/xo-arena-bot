import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# تفعيل نظام التنبيهات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تخزين حال مباريات اللاعبين (لوحة اللعب لكل محادثة)
games_state = {}

def get_board_keyboard(board):
    """إنشاء أزرار تفاعلية أنيقة وكبيرة للعبة XO"""
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            # تخصيص رموز تعبيرية أنيقة لكل حالة لتبدو غير مملة
            if cell == "X":
                text = "❌ X"
            elif cell == "O":
                text = "⭕ O"
            else:
                text = "⬜ فارغ"
            
            # تخزين الإحداثيات في البيانات المرتبطة بالزر
            row.append(InlineKeyboardButton(text, callback_data=f"play_{r}_{c}"))
        keyboard.append(row)
    
    # إضافة زر لإعادة تشغيل اللعبة بتصميم أنيق
    keyboard.append([InlineKeyboardButton("🔄 إعادة تشغيل اللعبة", callback_data="reset_game")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء اللعبة برسالة ترحيبية أنيقة"""
    chat_id = update.effective_chat.id
    games_state[chat_id] = [[" " for _ in range(3)] for _ in range(3)]
    
    user_name = update.effective_user.first_name
    welcome_text = (
        f"✨ أهلاً بك يا {user_name} في ساحة التحدي **XO Arena** 🎮\n\n"
        "لقد تم تجهيز لوحة اللعب بتصميم أنيق ومميز. ابدأ بالضغط على المربعات أدناه للعب!"
    )
    
    keyboard = get_board_keyboard(games_state[chat_id])
    await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع ضغطات الأزرار وتحديث اللوحة"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    data = query.data
    
    if chat_id not in games_state:
        games_state[chat_id] = [[" " for _ in range(3)] for _ in range(3)]
    
    board = games_state[chat_id]
    
    if data == "reset_game":
        games_state[chat_id] = [[" " for _ in range(3)] for _ in range(3)]
        await query.edit_message_text(
            text="🔄 تم إعادة تعيين اللوحة بنجاح. لنبدأ من جديد!",
            reply_markup=get_board_keyboard(games_state[chat_id])
        )
        return

    if data.startswith("play_"):
        _, r, c = data.split("_")
        r, c = int(r), int(c)
        
        if board[r][c] == " ":
            board[r][c] = "X" # يمكنك تخصيص دور اللاعبين هنا لاحقاً
            await query.edit_message_text(
                text="🎮 ساحة التحدي قائمة - استمر في اللعب:",
                reply_markup=get_board_keyboard(board)
            )
        else:
            await query.answer("⚠️ هذا المربع محجوز مسبقاً، اختر مربعاً آخر!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت في متغيرات البيئة!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    print("XO ARENA - Interactive Mode Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
