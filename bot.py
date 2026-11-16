import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, InlineQueryHandler
from uuid import uuid4

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# تخزين حالات الألعاب والنتائج المرتبطة حصرياً بـ inline_message_id
inline_games = {}

def check_winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != " ":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] != " ":
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != " ":
        return board[0][2]
    if all(cell != " " for row in board for cell in row):
        return "Tie"
    return None

def get_fancy_board(board):
    """تصميم مربعات عريض ومرتب وأنيق"""
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if cell == "X":
                text = "❌"
            elif cell == "O":
                text = "⭕"
            else:
                text = "▪️"  # مربعات فارغة وأنيقة
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 ── إعادة ضبط المعركة ── 🔄", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

def get_game_text(scores, turn_name, status_msg=""):
    """توليد النص الاحترافي مع العداد تماماً مثل الصورة"""
    x_score = scores["X"]
    o_score = scores["O"]
    ties = scores["ties"]
    
    text = (
        "🎮 **لوحة التحدي الكبرى (X-O)** 🕹️\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📊 **لوحة النتيجة الحالية:** 📊\n"
        f"👑 أبو مِيلاف: {x_score} | 🎯 أم مِيلاف: {o_score} | 🤝 تعادل: {ties}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
    )
    
    if status_msg:
        text += f"{status_msg}\n"
    else:
        turn_str = "دور اللاعب الحالي: أبو مِيلاف 👑 (❌)" if turn_name == "X" else "دور اللاعب الحالي: أم مِيلاف 🎯 (⭕)"
        text += f"{turn_str}\n"
        
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎮 **لوحة التحدي الكبرى (X-O)** 🎮\n\n"
        "اكتب في محادثة صديقك:\n"
        "`@Blend_XO_Game_Bot` وحط مسافة لبدء المعركة!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    
    game_id = str(uuid4())
    board = [[" " for _ in range(3)] for _ in range(3)]
    
    # تهيئة اللعبة في الذاكرة
    inline_games[game_id] = {
        "board": board,
        "turn": "X",
        "scores": {"X": 0, "O": 0, "ties": 0}
    }
    
    text = get_game_text(inline_games[game_id]["scores"], "X")
    
    results = [
        InlineQueryResultArticle(
            id=game_id,
            title="🎮 ابدأ لوحة التحدي الكبرى (X-O)",
            description="اضغط هنا لإرسال اللعبة مع استجابة فورية مضمونة",
            input_message_content=InputTextMessageContent(
                message_text=text,
                parse_mode="Markdown"
            ),
            reply_markup=get_fancy_board(board)
        )
    ]
    await query.answer(results, cache_time=0)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    inline_message_id = query.inline_message_id
    
    if not inline_message_id:
        return

    # عندما يتم إرسال اللعبة وتثبيتها في الشات، تيليجرام يمنحها inline_message_id جديد
    # لذا إذا لم يكن موجوداً في القاموس، نقوم بإنشاء حالة افتراضية جديدة له فوراً لكي لا يتوقف التفاعل
    if inline_message_id not in inline_games:
        inline_games[inline_message_id] = {
            "board": [[" " for _ in range(3)] for _ in range(3)],
            "turn": "X",
            "scores": {"X": 0, "O": 0, "ties": 0}
        }
    
    game = inline_games[inline_message_id]
    board = game["board"]
    current_turn = game["turn"]
    scores = game["scores"]

    if data == "action_reset":
        game["board"] = [[" " for _ in range(3)] for _ in range(3)]
        game["turn"] = "X"
        text = get_game_text(scores, "X", "🔄 **بدأت جولة جديدة! التحدي مستمر**")
        await context.bot.edit_message_text(
            inline_message_id=inline_message_id,
            text=text,
            reply_markup=get_fancy_board(game["board"]),
            parse_mode="Markdown"
        )
        return

    if data.startswith("cell_"):
        _, r, c = data.split("_")
        r, c = int(r), int(c)
        
        if board[r][c] == " ":
            board[r][c] = current_turn
            winner = check_winner(board)
            
            if winner:
                if winner == "X":
                    scores["X"] += 1
                    status_msg = "🎉 **فاز في الجولة: أبو مِيلاف 👑 (❌)!**"
                elif winner == "O":
                    scores["O"] += 1
                    status_msg = "🎉 **فاز في الجولة: أم مِيلاف 🎯 (⭕)!**"
                else:
                    scores["ties"] += 1
                    status_msg = "🤝 **تعادلت المعركة بينكم!**"
                
                # إعادة ضبط اللوحة للجولة التالية مع الاحتفاظ بالنقاط
                game["board"] = [[" " for _ in range(3)] for _ in range(3)]
                game["turn"] = "X"
                text = get_game_text(scores, "X", f"{status_msg}\n👇 اضغط على المربعات للجولة التالية:")
            else:
                # تبديل الدور
                game["turn"] = "O" if current_turn == "X" else "X"
                text = get_game_text(scores, game["turn"])
            
            await context.bot.edit_message_text(
                inline_message_id=inline_message_id,
                text=text,
                reply_markup=get_fancy_board(board),
                parse_mode="Markdown"
            )
        else:
            await query.answer("⚠️ هذا المربع محجوز يا بطل!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت!")
        return
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("XO Arena Secure Inline Pro is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
