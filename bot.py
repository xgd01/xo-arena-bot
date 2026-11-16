import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# تفعيل نظام التنبيهات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تخزين حالة اللعبة لكل محادثة (اللوحة، اللاعبين، ومن الدور عليه)
games_state = {}

def get_board_keyboard(board):
    """إنشاء أزرار تفاعلية أنيقة وكبيرة للوحة XO"""
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if cell == "X":
                text = "❌ أبو مِيلاف"
            elif cell == "O":
                text = "⭕ أم مِيلاف"
            else:
                text = "⬛ ··· فارغ ···"
            
            row.append(InlineKeyboardButton(text, callback_data=f"play_{r}_{c}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 إعادة تشغيل ساحة التحدي", callback_data="reset_game")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء لعبة جديدة ثنائية بين أبو مِيلاف وأم مِيلاف"""
    chat_id = update.effective_chat.id
    
    # تهيئة اللوحة فارغة، وتحديد أن اللاعب الأول هو أبو مِيلاف (X)
    games_state[chat_id] = {
        "board": [[" " for _ in range(3)] for _ in range(3)],
        "turn": "X",  # X يمثل أبو مِيلاف، O يمثل أم مِيلاف
        "player_x": None,
        "player_o": None
    }
    
    welcome_text = (
        "🔥 **معركة ساحة التحدي | XO Arena** 🔥\n\n"
        "🎮 اللاعب الأول: **أبو مِيلاف** (❌)\n"
        "🎮 اللاعب الثاني: **أم مِيلاف** (⭕)\n\n"
        "⚡ الدور الحالي لـ: **أبو مِيلاف (❌)**\n"
        "اضغط على أي مربع أدناه للبدء باللعب!"
    )
    
    keyboard = get_board_keyboard(games_state[chat_id]["board"])
    await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع ضغطات الأزرار والتبديل بين اللاعبين"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    user = query.from_user
    data = query.data
    
    if chat_id not in games_state:
        games_state[chat_id] = {
            "board": [[" " for _ in range(3)] for _ in range(3)],
            "turn": "X",
            "player_x": None,
            "player_o": None
        }
    
    game = games_state[chat_id]
    board = game["board"]
    
    if data == "reset_game":
        game["board"] = [[" " for _ in range(3)] for _ in range(3)]
        game["turn"] = "X"
        game["player_x"] = None
        game["player_o"] = None
        
        text = (
            "🔄 **تم إعادة تعيين ساحة التحدي!**\n\n"
            "🎮 اللاعب الأول: **أبو مِيلاف** (❌)\n"
            "🎮 اللاعب الثاني: **أم مِيلاف** (⭕)\n\n"
            "⚡ الدور الحالي لـ: **أبو مِيلاف (❌)**"
        )
        await query.edit_message_text(text=text, reply_markup=get_board_keyboard(board), parse_mode="Markdown")
        return

    if data.startswith("play_"):
        _, r, c = data.split("_")
        r, c = int(r), int(c)
        
        # تسجيل اللاعبين تلقائياً عند أول ضغطة
        if game["turn"] == "X":
            if not game["player_x"]:
                game["player_x"] = user.id
        else:
            if not game["player_o"]:
                game["player_o"] = user.id

        # التحقق إن كان المربع فارغاً
        if board[r][c] == " ":
            board[r][c] = game["turn"]
            
            # تبديل الدور بين أبو مِيلاف وأم مِيلاف
            if game["turn"] == "X":
                game["turn"] = "O"
                current_name = "أم مِيلاف (⭕)"
            else:
                game["turn"] = "X"
                current_name = "أبو مِيلاف (❌)"
            
            status_text = (
                "⚔️ **مستمرة المعركة في XO Arena** ⚔️\n\n"
                "🎮 اللاعب الأول: **أبو مِيلاف** (❌)\n"
                "🎮 اللاعب الثاني: **أم مِيلاف** (⭕)\n\n"
                f"⚡ الدور الحالي لـ: **{current_name}**"
            )
            
            await query.edit_message_text(
                text=status_text,
                reply_markup=get_board_keyboard(board),
                parse_mode="Markdown"
            )
        else:
            await query.answer("⚠️ هذا المربع محجوز مسبقاً يا بطل، اختر مربعاً آخر!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت في متغيرات البيئة!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    print("XO ARENA - Multiplayer Mode Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
