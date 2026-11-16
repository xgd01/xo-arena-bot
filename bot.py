import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, InlineQueryHandler
from uuid import uuid4

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# تخزين حالات الألعاب النشطة للإنلاين لضمان سرعة الاستجابة والدقة
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
    """تصميم فخم، عريض، وواضحة جداً للعين"""
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if cell == "X":
                text = "❌ [ أبو مِيلاف ]"
            elif cell == "O":
                text = "⭕ [ أم مِيلاف ]"
            else:
                text = "⬛ [ فارغ ] ⬛"
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 ── إعادة ضبط المعركة ── 🔄", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 **XO ARENA - ساحة التحدي** 🔥\n\n"
        "🎮 **طريقة اللعب:**\n"
        "اكتب في محادثة صديقك:\n"
        "`@Blend_XO_Game_Bot` وحط مسافة، ثم اختر اللعبة وابدؤوا التحدي!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    
    game_id = str(uuid4())
    board = [[" " for _ in range(3)] for _ in range(3)]
    
    # حفظ حالة اللعبة في الذاكرة لتتبعها بدقة
    inline_games[game_id] = {
        "board": board,
        "turn": "X"
    }
    
    text = (
        "⚔️ **معركة XO ARENA الكبرى** ⚔️\n\n"
        "🏆 اللاعب الأول: أبو مِيلاف (❌)\n"
        "🏆 اللاعب الثاني: أم مِيلاف (⭕)\n\n"
        "⚡ **الدور الحالي:** أبو مِيلاف (❌)"
    )
    
    results = [
        InlineQueryResultArticle(
            id=game_id,
            title="🎮 ابدأ معركة XO Arena المحدثة",
            description="اضغط هنا لإرسال لوحة اللعب الفخمة والجديدة مع صديقك",
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
        # إذا كانت اللعبة مرسلة بطريقة عادية
        return

    # البحث عن حالة اللعبة أو تهيئتها إن لم تكن مخزنة
    if inline_message_id not in inline_games:
        inline_games[inline_message_id] = {
            "board": [[" " for _ in range(3)] for _ in range(3)],
            "turn": "X"
        }
    
    game = inline_games[inline_message_id]
    board = game["board"]
    current_turn = game["turn"]

    if data == "action_reset":
        game["board"] = [[" " for _ in range(3)] for _ in range(3)]
        game["turn"] = "X"
        text = (
            "🔄 **بدأت جولة جديدة!**\n\n"
            "🏆 اللاعب الأول: أبو مِيلاف (❌)\n"
            "🏆 اللاعب الثاني: أم مِيلاف (⭕)\n\n"
            "⚡ **الدور الحالي:** أبو مِيلاف (❌)"
        )
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
                    msg = "🎉 **فاز في الجولة: أبو مِيلاف (❌)!** 🏆"
                elif winner == "O":
                    msg = "🎉 **فاز في الجولة: أم مِيلاف (⭕)!** 🏆"
                else:
                    msg = "🤝 **تعادلت المعركة! لا يوجد فائز.**"
                
                text = f"🏁 **انتهت الجولة!**\n\n{msg}\n\n👇 اضغط على زر إعادة الضبط لجولة جديدة."
            else:
                # تبديل الدور
                game["turn"] = "O" if current_turn == "X" else "X"
                next_name = "أم مِيلاف (⭕)" if game["turn"] == "O" else "أبو مِيلاف (❌)"
                text = (
                    "⚔️ **معركة XO ARENA جارية** ⚔️\n\n"
                    "🏆 اللاعب الأول: أبو مِيلاف (❌)\n"
                    "🏆 اللاعب الثاني: أم مِيلاف (⭕)\n\n"
                    f"⚡ **الدور الحالي:** {next_name}"
                )
            
            await context.bot.edit_message_text(
                inline_message_id=inline_message_id,
                text=text,
                reply_markup=get_fancy_board(board),
                parse_mode="Markdown"
            )
        else:
            await query.answer("⚠️ هذا المربع محجوز يا بطل، اختر مكاناً آخر!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت!")
        return
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("XO Arena Interactive Pro is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
