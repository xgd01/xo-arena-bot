import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

games_state = {}

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
                text = "⬛ فارغ"
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 جولة جديدة", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if chat_id not in games_state:
        games_state[chat_id] = {"scores": {"X": 0, "O": 0, "ties": 0}}
        
    games_state[chat_id].update({
        "board": [[" " for _ in range(3)] for _ in range(3)],
        "turn": "X",
        "player_x": {"id": user.id, "name": user.first_name},
        "player_o": None,
        "status": "waiting",
        "game_over": False
    })
    
    game = games_state[chat_id]
    scores = game["scores"]
    
    text = (
        "🔥 **XO ARENA - ساحة التحدي** 🔥\n\n"
        f"🏆 النقاط: ❌ أبو مِيلاف ({scores['X']}) | ⭕ أم مِيلاف ({scores['O']}) | التعادل ({scores['ties']})\n\n"
        f"👑 اللاعب الأول: {game['player_x']['name']} (أبو مِيلاف)\n"
        "⏳ اللاعب الثاني: في انتظار انضمام الخصم...\n\n"
        "👇 اضغط على الزر أدناه للانضمام كـ (أم مِيلاف)!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎮 انضم الآن كـ (أم مِيلاف ⭕)", callback_data="action_join")],
        [InlineKeyboardButton("🔄 إعادة ضبط", callback_data="action_reset")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    user = query.from_user
    data = query.data
    
    if chat_id not in games_state:
        return
    game = games_state[chat_id]
    scores = game["scores"]
    
    if data == "action_join":
        if game["player_o"] is None:
            if user.id == game["player_x"]["id"]:
                await query.answer("⚠️ لا يمكنك اللعب ضد نفسك!", show_alert=True)
                return
            game["player_o"] = {"id": user.id, "name": user.first_name}
            game["status"] = "playing"
            
            text = (
                "⚔️ **بدأت المعركة الرسمية!** ⚔️\n\n"
                f"❌ أبو مِيلاف: {game['player_x']['name']}\n"
                f"⭕ أم مِيلاف: {game['player_o']['name']}\n\n"
                "⚡ الدور الحالي: أبو مِيلاف (❌)"
            )
            await query.edit_message_text(text=text, reply_markup=get_fancy_board(game["board"]), parse_mode="Markdown")
        else:
            await query.answer(f"✅ المقعد محجوز لـ {game['player_o']['name']}", show_alert=True)
        return

    if data == "action_reset":
        game["board"] = [[" " for _ in range(3)] for _ in range(3)]
        game["turn"] = "X"
        game["game_over"] = False
        text = "🔄 **جولة جديدة بدأت!**\n\n⚡ الدور الحالي: أبو مِيلاف (❌)"
        await query.edit_message_text(text=text, reply_markup=get_fancy_board(game["board"]), parse_mode="Markdown")
        return

    if data.startswith("cell_"):
        if game["status"] == "waiting":
            await query.answer("⏳ انتظر انضمام أم مِيلاف أولاً!", show_alert=True)
            return
        if game["game_over"]:
            await query.answer("⚠️ انتهت الجولة، اضغط جولة جديدة!", show_alert=True)
            return
            
        is_x = user.id == game["player_x"]["id"]
        is_o = game["player_o"] and user.id == game["player_o"]["id"]
        
        if not is_x and not is_o:
            await query.answer("👀 أنت متفرج في هذه المباراة!", show_alert=True)
            return
        if game["turn"] == "X" and not is_x:
            await query.answer("⏳ ليس دورك، انتظر أبو مِيلاف!", show_alert=True)
            return
        if game["turn"] == "O" and not is_o:
            await query.answer("⏳ ليس دورك، انتظر أم مِيلاف!", show_alert=True)
            return

        _, r, c = data.split("_")
        r, c = int(r), int(c)
        board = game["board"]
        
        if board[r][c] == " ":
            board[r][c] = game["turn"]
            winner = check_winner(board)
            
            if winner:
                game["game_over"] = True
                if winner == "X":
                    scores["X"] += 1
                    msg = "🎉 **فاز في الجولة: أبو مِيلاف (❌)!**"
                elif winner == "O":
                    scores["O"] += 1
                    msg = "🎉 **فاز في الجولة: أم مِيلاف (⭕)!**"
                else:
                    scores["ties"] += 1
                    msg = "🤝 **تعادلت المعركة!**"
                    
                text = (
                    f"🏁 **انتهت الجولة!**\n\n{msg}\n\n"
                    f"🏆 النقاط: ❌ ({scores['X']}) | ⭕ ({scores['O']}) | تعادل ({scores['ties']})\n\n"
                    "👇 اضغط جولة جديدة للبدء!"
                )
            else:
                game["turn"] = "O" if game["turn"] == "X" else "X"
                next_name = "أم مِيلاف (⭕)" if game["turn"] == "O" else "أبو مِيلاف (❌)"
                text = f"⚔️ **المعركة مستمرة**\n\n⚡ الدور الحالي: {next_name}"
                
            await query.edit_message_text(text=text, reply_markup=get_fancy_board(board), parse_mode="Markdown")
        else:
            await query.answer("⚠️ هذا المربع محجوز!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت!")
        return
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
